"""Broker Account Management API endpoints."""

import logging
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.orm_models import BrokerAccount, User

logger = logging.getLogger(__name__)

router = APIRouter()


class BrokerAccountCreate(BaseModel):
    """Schema for creating a broker account."""
    broker_name: str = Field(..., description="Broker name (exness, justmarkets, mt5, paper)")
    account_id: Optional[str] = Field(None, description="Account ID/Login for the broker")
    api_key: Optional[str] = Field(None, description="API key or token")
    api_secret: Optional[str] = Field(None, description="API secret if needed")
    base_url: Optional[str] = Field(None, description="Custom base URL")
    mt5_path: Optional[str] = Field(None, description="MT5 terminal path")
    mt5_password: Optional[str] = Field(None, description="MT5 password")


class BrokerAccountResponse(BaseModel):
    """Schema for broker account response."""
    id: int
    user_id: int
    broker_name: str
    account_id: Optional[str] = None
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    base_url: Optional[str] = None
    is_active: int
    created_at: datetime
    updated_at: datetime
    mt5_path: Optional[str] = None
    mt5_password: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


@router.post("/brokers/accounts", response_model=BrokerAccountResponse)
def create_broker_account(
    account_data: BrokerAccountCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> BrokerAccountResponse:
    """Create a new broker account for the current user.

    **Parameters:**
    - `broker_name`: Broker name (exness, justmarkets, mt5, paper)
    - `account_id`: Account ID/Login (optional)
    - `api_key`: API key or token (optional)
    - `api_secret`: API secret (optional)
    - `base_url`: Custom base URL (optional)
    - `mt5_path`: MT5 terminal path (optional, for MT5 only)
    - `mt5_password`: MT5 password (optional, for MT5 only)

    **Response:** Broker account details
    """
    try:
        print(f"Creating broker account for user {current_user.id}: {account_data.broker_name}")
        
        # Validate broker name
        valid_brokers = ["exness", "justmarkets", "mt5", "paper"]
        if account_data.broker_name not in valid_brokers:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid broker name. Must be one of: {', '.join(valid_brokers)}"
            )

        # Check if user already has an account for this broker
        existing = db.query(BrokerAccount).filter(
            BrokerAccount.user_id == current_user.id,
            BrokerAccount.broker_name == account_data.broker_name
        ).first()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"You already have a {account_data.broker_name} account configured"
            )

        # Create new broker account
        broker_account = BrokerAccount(
            user_id=current_user.id,
            broker_name=account_data.broker_name,
            account_id=account_data.account_id,
            api_key=account_data.api_key,
            api_secret=account_data.api_secret,
            base_url=account_data.base_url,
            mt5_path=account_data.mt5_path,
            mt5_password=account_data.mt5_password,
            is_active=1
        )

        print(f"Adding broker account to DB: {broker_account}")
        db.add(broker_account)
        db.commit()
        db.refresh(broker_account)

        print(f"Created {account_data.broker_name} account for user {current_user.id}")
        return BrokerAccountResponse.from_orm(broker_account)

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error creating broker account: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create broker account: {str(e)}"
        )


@router.get("/brokers/accounts", response_model=List[BrokerAccountResponse])
async def list_broker_accounts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> List[BrokerAccountResponse]:
    """List all broker accounts for the current user.

    **Response:** List of broker accounts
    """
    try:
        accounts = db.query(BrokerAccount).filter(
            BrokerAccount.user_id == current_user.id
        ).all()

        return [BrokerAccountResponse.from_orm(account) for account in accounts]

    except Exception as e:
        logger.error(f"Error listing broker accounts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list broker accounts: {str(e)}"
        )


@router.get("/brokers/accounts/{account_id}", response_model=BrokerAccountResponse)
async def get_broker_account(
    account_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> BrokerAccountResponse:
    """Get a specific broker account by ID.

    **Parameters:**
    - `account_id`: Broker account ID

    **Response:** Broker account details
    """
    try:
        account = db.query(BrokerAccount).filter(
            BrokerAccount.id == account_id,
            BrokerAccount.user_id == current_user.id
        ).first()

        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Broker account not found"
            )

        return BrokerAccountResponse.from_orm(account)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting broker account: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get broker account: {str(e)}"
        )


@router.put("/brokers/accounts/{account_id}", response_model=BrokerAccountResponse)
async def update_broker_account(
    account_id: int,
    account_data: BrokerAccountCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> BrokerAccountResponse:
    """Update a broker account.

    **Parameters:**
    - `account_id`: Broker account ID
    - Update data in request body

    **Response:** Updated broker account details
    """
    try:
        account = db.query(BrokerAccount).filter(
            BrokerAccount.id == account_id,
            BrokerAccount.user_id == current_user.id
        ).first()

        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Broker account not found"
            )

        # Update fields
        for field, value in account_data.dict(exclude_unset=True).items():
            setattr(account, field, value)

        db.commit()
        db.refresh(account)

        logger.info(f"Updated {account.broker_name} account {account_id} for user {current_user.id}")
        return BrokerAccountResponse.from_orm(account)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating broker account: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update broker account: {str(e)}"
        )


@router.delete("/brokers/accounts/{account_id}")
async def delete_broker_account(
    account_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a broker account.

    **Parameters:**
    - `account_id`: Broker account ID

    **Response:** Success message
    """
    try:
        account = db.query(BrokerAccount).filter(
            BrokerAccount.id == account_id,
            BrokerAccount.user_id == current_user.id
        ).first()

        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Broker account not found"
            )

        db.delete(account)
        db.commit()

        logger.info(f"Deleted {account.broker_name} account {account_id} for user {current_user.id}")
        return {"message": "Broker account deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting broker account: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete broker account: {str(e)}"
        )


@router.put("/brokers/accounts/{account_id}/activate")
async def activate_broker_account(
    account_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Activate a broker account (set as active).

    **Parameters:**
    - `account_id`: Broker account ID

    **Response:** Success message
    """
    try:
        account = db.query(BrokerAccount).filter(
            BrokerAccount.id == account_id,
            BrokerAccount.user_id == current_user.id
        ).first()

        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Broker account not found"
            )

        # Deactivate all other accounts for this broker
        db.query(BrokerAccount).filter(
            BrokerAccount.user_id == current_user.id,
            BrokerAccount.broker_name == account.broker_name
        ).update({"is_active": 0})

        # Activate this account
        account.is_active = 1
        db.commit()

        logger.info(f"Activated {account.broker_name} account {account_id} for user {current_user.id}")
        return {"message": f"{account.broker_name} account activated successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error activating broker account: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to activate broker account: {str(e)}"
        )