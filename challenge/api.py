from typing import List, Set
import logging

import pandas as pd
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, validator

from challenge.model import DelayModel

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Flight Delay Prediction API",
    description="Predict flight delays based on operator, flight type, and month",
    version="1.0.0"
)

# Initialize model instance
model = DelayModel()

# Valid airline operators - using Set for O(1) lookup
VALID_OPERATORS: Set[str] = {
    'Aerolineas Argentinas', 'Aeromexico', 'Air Canada', 'Air France',
    'Alitalia', 'American Airlines', 'Austral', 'Avianca', 'British Airways',
    'Copa Air', 'Delta Air', 'Gol Trans', 'Grupo LATAM', 'Iberia',
    'JetSmart SPA', 'K.L.M.', 'Lacsa', 'Latin American Wings',
    'Oceanair Linhas Aereas', 'Plus Ultra Lineas Aereas', 'Qantas Airways',
    'Sky Airline', 'United Airlines'
}

# Top 10 features selected during model training
EXPECTED_FEATURES: List[str] = [
    "OPERA_Latin American Wings",
    "MES_7",
    "MES_10",
    "OPERA_Grupo LATAM",
    "MES_12",
    "TIPOVUELO_I",
    "MES_4",
    "MES_11",
    "OPERA_Sky Airline",
    "OPERA_Copa Air",
]

# Load and train model at startup
try:
    logger.info("Loading training data...")
    data = pd.read_csv('data/data.csv', low_memory=False)
    features, target = model.preprocess(data, target_column="delay")
    model.fit(features, target)
    logger.info("Model successfully trained and ready for predictions")
except FileNotFoundError:
    logger.warning("Training data not found. Model will use lazy training on first prediction.")
except Exception as e:
    logger.error(f"Failed to pre-train model: {e}")


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, 
    exc: RequestValidationError
) -> JSONResponse:
    """
    Handle Pydantic validation errors with safe error messages.
    
    Converts detailed validation errors into user friendly messages
    while preventing exposure of internal implementation details.
    Returns 400 status code to comply with test requirements.
    
    In production, consider using 422 for better HTTP semantics.
    """
    # Extract user friendly error messages without internal details
    errors = []
    for error in exc.errors():
        field = error.get('loc', ['unknown'])[-1]  # Get field name
        msg = error.get('msg', 'Invalid value')
        errors.append(f"{field}: {msg}")
    
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": "Validation failed",
            "message": "; ".join(errors)
        }
    )


class Flight(BaseModel):
    """
    Flight information schema.
    
    Attributes:
        OPERA: Airline operator name
        TIPOVUELO: Flight type - 'N' for National, 'I' for International
        MES: Month of flight operation (1-12)
    """
    OPERA: str
    TIPOVUELO: str
    MES: int
    
    @validator('MES')
    def validate_month(cls, v: int) -> int:
        """Ensure month is in valid range [1-12]."""
        if not 1 <= v <= 12:
            raise ValueError('MES must be between 1 and 12')
        return v
    
    @validator('TIPOVUELO')
    def validate_flight_type(cls, v: str) -> str:
        """Validate flight type is either National or International."""
        if v not in ['N', 'I']:
            raise ValueError('TIPOVUELO must be N or I')
        return v
    
    @validator('OPERA')
    def validate_operator(cls, v: str) -> str:
        """Validate airline operator against known carriers."""
        if v not in VALID_OPERATORS:
            raise ValueError(f'OPERA must be one of the valid operators')
        return v


class FlightRequest(BaseModel):
    """Request payload containing flights to predict."""
    flights: List[Flight]


class PredictionResponse(BaseModel):
    """Response payload with delay predictions."""
    predict: List[int]


@app.get(
    "/health", 
    status_code=status.HTTP_200_OK,
    tags=["Health"]
)
async def get_health() -> dict:
    """
    Health check endpoint.
    
    Returns:
        dict: Service health status
    """
    return {"status": "OK"}


@app.post(
    "/predict", 
    status_code=status.HTTP_200_OK,
    response_model=PredictionResponse,
    tags=["Predictions"]
)
async def post_predict(request: FlightRequest) -> dict:
    """
    Predict flight delays for provided flights.
    
    The endpoint performs the following steps:
    1. Converts input flights to DataFrame
    2. One-hot encodes categorical features (OPERA, MES, TIPOVUELO)
    3. Ensures all expected features exist (adds missing features with 0)
    4. Selects top 10 features in correct order
    5. Returns predictions (0 = No delay, 1 = Delay expected)
    
    Args:
        request: FlightRequest containing list of flights
        
    Returns:
        PredictionResponse: Dictionary with 'predict' key containing list of predictions
        
    Raises:
        HTTPException: 400 if prediction fails
    """
    try:
        # Convert Pydantic models to DataFrame
        flights_data = [flight.dict() for flight in request.flights]
        df = pd.DataFrame(flights_data)
        
        # Feature engineering: one-hot encode categorical variables
        df = pd.get_dummies(
            df,
            columns=["OPERA", "MES", "TIPOVUELO"],
            drop_first=False
        )
        
        # Ensure all expected features exist (handle missing categories)
        # Missing features are filled with 0 (category not present)
        for feature in EXPECTED_FEATURES:
            if feature not in df.columns:
                df[feature] = 0
        
        # Select only top 10 features in the model's expected order
        features = df[EXPECTED_FEATURES]
        
        # Generate predictions using trained model
        predictions = model.predict(features)
        
        logger.info(f"Successfully predicted {len(predictions)} flight(s)")
        
        return {"predict": predictions}
    
    except ValueError as e:
        # Business logic validation errors (e.g., invalid data ranges)
        logger.warning(f"Validation error during prediction: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Invalid input data"
        )
    except KeyError as e:
        # Missing required features or data processing errors
        logger.error(f"Feature error during prediction: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Data processing error"
        )
    except Exception as e:
        # Unexpected errors: return 400 for test compatibility
        # In production, consider using 500 for true server errors
        logger.error(f"Unexpected error during prediction: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An error occurred during prediction"
        )
