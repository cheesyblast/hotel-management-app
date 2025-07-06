from fastapi import FastAPI, APIRouter, HTTPException, status, Response
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, date
from enum import Enum
import io
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Enums
class RoomStatus(str, Enum):
    AVAILABLE = "available"
    OCCUPIED = "occupied"
    MAINTENANCE = "maintenance"
    CLEANING = "cleaning"

class RoomType(str, Enum):
    SINGLE = "single"
    DOUBLE = "double"
    SUITE = "suite"
    DELUXE = "deluxe"

class BookingStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CHECKED_IN = "checked_in"
    CHECKED_OUT = "checked_out"
    CANCELLED = "cancelled"

class PaymentType(str, Enum):
    CASH = "cash"
    CARD = "card"

class PaymentStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    REFUNDED = "refunded"

class ExpenseCategory(str, Enum):
    UTILITIES = "utilities"
    MAINTENANCE = "maintenance"
    SUPPLIES = "supplies"
    STAFF = "staff"
    MARKETING = "marketing"
    OTHER = "other"

# Data Models
class Room(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    room_number: str
    room_type: RoomType
    price_per_night: float
    status: RoomStatus = RoomStatus.AVAILABLE
    description: Optional[str] = None
    max_occupancy: int = 2
    amenities: List[str] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)

class RoomCreate(BaseModel):
    room_number: str
    room_type: RoomType
    price_per_night: float
    description: Optional[str] = None
    max_occupancy: int = 2
    amenities: List[str] = []

class RoomUpdate(BaseModel):
    room_type: Optional[RoomType] = None
    price_per_night: Optional[float] = None
    status: Optional[RoomStatus] = None
    description: Optional[str] = None
    max_occupancy: Optional[int] = None
    amenities: Optional[List[str]] = None

class Guest(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    email: str
    phone: str
    address: Optional[str] = None
    country: str = "Unknown"
    id_number: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class GuestCreate(BaseModel):
    name: str
    email: str
    phone: str
    address: Optional[str] = None
    country: str = "Unknown"
    id_number: Optional[str] = None

class Payment(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    booking_id: str
    payment_type: PaymentType
    amount: float
    payment_date: datetime = Field(default_factory=datetime.utcnow)
    status: PaymentStatus = PaymentStatus.COMPLETED
    description: Optional[str] = None
    is_advance: bool = False

class PaymentCreate(BaseModel):
    booking_id: str
    payment_type: PaymentType
    amount: float
    description: Optional[str] = None
    is_advance: bool = False

class Expense(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    category: ExpenseCategory
    amount: float
    description: str
    expense_date: date = Field(default_factory=date.today)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ExpenseCreate(BaseModel):
    category: ExpenseCategory
    amount: float
    description: str
    expense_date: Optional[date] = None

class Invoice(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    booking_id: str
    guest_name: str
    room_number: str
    check_in_date: date
    check_out_date: date
    total_amount: float
    advance_paid: float
    balance_due: float
    payments: List[Payment] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)

class FinancialReport(BaseModel):
    date: date
    total_income: float
    total_expenses: float
    net_profit: float
    total_bookings: int
    room_revenue: float
    advance_payments: float
    final_payments: float
    expenses_by_category: Dict[str, float]

class Booking(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    guest_id: str
    room_id: str
    check_in_date: date
    check_out_date: date
    status: BookingStatus = BookingStatus.PENDING
    total_amount: float
    special_requests: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Convert date objects to strings for MongoDB storage
    def dict(self, *args, **kwargs):
        data = super().dict(*args, **kwargs)
        if 'check_in_date' in data and isinstance(data['check_in_date'], date):
            data['check_in_date'] = data['check_in_date'].isoformat()
        if 'check_out_date' in data and isinstance(data['check_out_date'], date):
            data['check_out_date'] = data['check_out_date'].isoformat()
        return data

class BookingCreate(BaseModel):
    guest_id: str
    room_id: str
    check_in_date: date
    check_out_date: date
    special_requests: Optional[str] = None

    @validator('check_out_date')
    def check_out_after_check_in(cls, v, values):
        if 'check_in_date' in values and v <= values['check_in_date']:
            raise ValueError('Check-out date must be after check-in date')
        return v
    
    # Convert date objects to strings for MongoDB storage
    def dict(self, *args, **kwargs):
        data = super().dict(*args, **kwargs)
        if 'check_in_date' in data and isinstance(data['check_in_date'], date):
            data['check_in_date'] = data['check_in_date'].isoformat()
        if 'check_out_date' in data and isinstance(data['check_out_date'], date):
            data['check_out_date'] = data['check_out_date'].isoformat()
        return data

class BookingUpdate(BaseModel):
    status: Optional[BookingStatus] = None
    special_requests: Optional[str] = None

class DashboardStats(BaseModel):
    total_rooms: int
    available_rooms: int
    occupied_rooms: int
    maintenance_rooms: int
    cleaning_rooms: int
    today_checkins: int
    today_checkouts: int
    total_revenue: float

# Helper functions
async def check_room_availability(room_id: str, check_in: date, check_out: date, exclude_booking_id: str = None) -> bool:
    """Check if a room is available for the given date range"""
    # Convert date objects to strings for MongoDB
    check_in_str = check_in.isoformat() if isinstance(check_in, date) else check_in
    check_out_str = check_out.isoformat() if isinstance(check_out, date) else check_out
    
    query = {
        "room_id": room_id,
        "status": {"$in": [BookingStatus.CONFIRMED, BookingStatus.CHECKED_IN]},
        "$or": [
            {"check_in_date": {"$lt": check_out_str}, "check_out_date": {"$gt": check_in_str}},
        ]
    }
    
    if exclude_booking_id:
        query["id"] = {"$ne": exclude_booking_id}
    
    existing_booking = await db.bookings.find_one(query)
    return existing_booking is None

async def calculate_booking_amount(room_id: str, check_in: date, check_out: date) -> float:
    """Calculate total amount for a booking"""
    room = await db.rooms.find_one({"id": room_id})
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    # If check_in and check_out are strings, convert them to date objects
    if isinstance(check_in, str):
        check_in = date.fromisoformat(check_in)
    if isinstance(check_out, str):
        check_out = date.fromisoformat(check_out)
    
    nights = (check_out - check_in).days
    return room["price_per_night"] * nights

# Room endpoints
@api_router.post("/rooms", response_model=Room)
async def create_room(room: RoomCreate):
    # Check if room number already exists
    existing_room = await db.rooms.find_one({"room_number": room.room_number})
    if existing_room:
        raise HTTPException(status_code=400, detail="Room number already exists")
    
    room_dict = room.dict()
    room_obj = Room(**room_dict)
    await db.rooms.insert_one(room_obj.dict())
    return room_obj

@api_router.get("/rooms", response_model=List[Room])
async def get_rooms():
    rooms = await db.rooms.find().to_list(100)
    return [Room(**room) for room in rooms]

@api_router.get("/rooms/{room_id}", response_model=Room)
async def get_room(room_id: str):
    room = await db.rooms.find_one({"id": room_id})
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    return Room(**room)

@api_router.put("/rooms/{room_id}", response_model=Room)
async def update_room(room_id: str, room_update: RoomUpdate):
    room = await db.rooms.find_one({"id": room_id})
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    update_data = room_update.dict(exclude_unset=True)
    if update_data:
        await db.rooms.update_one({"id": room_id}, {"$set": update_data})
    
    updated_room = await db.rooms.find_one({"id": room_id})
    return Room(**updated_room)

@api_router.delete("/rooms/{room_id}")
async def delete_room(room_id: str):
    room = await db.rooms.find_one({"id": room_id})
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    # Check if room has active bookings
    active_booking = await db.bookings.find_one({
        "room_id": room_id,
        "status": {"$in": [BookingStatus.CONFIRMED, BookingStatus.CHECKED_IN]}
    })
    if active_booking:
        raise HTTPException(status_code=400, detail="Cannot delete room with active bookings")
    
    await db.rooms.delete_one({"id": room_id})
    return {"message": "Room deleted successfully"}

# Guest endpoints
@api_router.post("/guests", response_model=Guest)
async def create_guest(guest: GuestCreate):
    # Check if email already exists
    existing_guest = await db.guests.find_one({"email": guest.email})
    if existing_guest:
        raise HTTPException(status_code=400, detail="Guest with this email already exists")
    
    guest_dict = guest.dict()
    guest_obj = Guest(**guest_dict)
    await db.guests.insert_one(guest_obj.dict())
    return guest_obj

@api_router.get("/guests", response_model=List[Guest])
async def get_guests():
    guests = await db.guests.find().to_list(100)
    return [Guest(**guest) for guest in guests]

@api_router.get("/guests/{guest_id}", response_model=Guest)
async def get_guest(guest_id: str):
    guest = await db.guests.find_one({"id": guest_id})
    if not guest:
        raise HTTPException(status_code=404, detail="Guest not found")
    return Guest(**guest)

@api_router.put("/guests/{guest_id}", response_model=Guest)
async def update_guest(guest_id: str, guest_update: GuestCreate):
    guest = await db.guests.find_one({"id": guest_id})
    if not guest:
        raise HTTPException(status_code=404, detail="Guest not found")
    
    # Check if email already exists for other guests
    if guest_update.email != guest["email"]:
        existing_guest = await db.guests.find_one({"email": guest_update.email, "id": {"$ne": guest_id}})
        if existing_guest:
            raise HTTPException(status_code=400, detail="Guest with this email already exists")
    
    update_data = guest_update.dict()
    await db.guests.update_one({"id": guest_id}, {"$set": update_data})
    
    updated_guest = await db.guests.find_one({"id": guest_id})
    return Guest(**updated_guest)

@api_router.delete("/guests/{guest_id}")
async def delete_guest(guest_id: str):
    guest = await db.guests.find_one({"id": guest_id})
    if not guest:
        raise HTTPException(status_code=404, detail="Guest not found")
    
    # Check if guest has active bookings
    active_booking = await db.bookings.find_one({
        "guest_id": guest_id,
        "status": {"$in": [BookingStatus.CONFIRMED, BookingStatus.CHECKED_IN]}
    })
    if active_booking:
        raise HTTPException(status_code=400, detail="Cannot delete guest with active bookings")
    
    await db.guests.delete_one({"id": guest_id})
    return {"message": "Guest deleted successfully"}

# Booking endpoints
@api_router.post("/bookings", response_model=Booking)
async def create_booking(booking: BookingCreate):
    # Validate guest exists
    guest = await db.guests.find_one({"id": booking.guest_id})
    if not guest:
        raise HTTPException(status_code=404, detail="Guest not found")
    
    # Validate room exists
    room = await db.rooms.find_one({"id": booking.room_id})
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    # Check room availability
    is_available = await check_room_availability(
        booking.room_id, 
        booking.check_in_date, 
        booking.check_out_date
    )
    if not is_available:
        raise HTTPException(status_code=400, detail="Room not available for selected dates")
    
    # Calculate total amount
    total_amount = await calculate_booking_amount(
        booking.room_id, 
        booking.check_in_date, 
        booking.check_out_date
    )
    
    booking_dict = booking.dict()
    booking_dict["total_amount"] = total_amount
    booking_obj = Booking(**booking_dict)
    await db.bookings.insert_one(booking_obj.dict())
    return booking_obj

@api_router.get("/bookings", response_model=List[Booking])
async def get_bookings():
    bookings = await db.bookings.find().to_list(100)
    return [Booking(**booking) for booking in bookings]

@api_router.get("/bookings/{booking_id}", response_model=Booking)
async def get_booking(booking_id: str):
    booking = await db.bookings.find_one({"id": booking_id})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    return Booking(**booking)

@api_router.put("/bookings/{booking_id}", response_model=Booking)
async def update_booking(booking_id: str, booking_update: BookingUpdate):
    booking = await db.bookings.find_one({"id": booking_id})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    update_data = booking_update.dict(exclude_unset=True)
    
    # Handle status changes
    if "status" in update_data:
        new_status = update_data["status"]
        current_status = booking["status"]
        
        # Update room status based on booking status
        if new_status == BookingStatus.CHECKED_IN and current_status == BookingStatus.CONFIRMED:
            await db.rooms.update_one(
                {"id": booking["room_id"]}, 
                {"$set": {"status": RoomStatus.OCCUPIED}}
            )
        elif new_status == BookingStatus.CHECKED_OUT and current_status == BookingStatus.CHECKED_IN:
            await db.rooms.update_one(
                {"id": booking["room_id"]}, 
                {"$set": {"status": RoomStatus.CLEANING}}
            )
        elif new_status == BookingStatus.CANCELLED:
            # If room was occupied, make it available for cleaning
            room = await db.rooms.find_one({"id": booking["room_id"]})
            if room and room["status"] == RoomStatus.OCCUPIED:
                await db.rooms.update_one(
                    {"id": booking["room_id"]}, 
                    {"$set": {"status": RoomStatus.CLEANING}}
                )
    
    if update_data:
        await db.bookings.update_one({"id": booking_id}, {"$set": update_data})
    
    updated_booking = await db.bookings.find_one({"id": booking_id})
    return Booking(**updated_booking)

@api_router.delete("/bookings/{booking_id}")
async def delete_booking(booking_id: str):
    booking = await db.bookings.find_one({"id": booking_id})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    await db.bookings.delete_one({"id": booking_id})
    return {"message": "Booking deleted successfully"}

# Dashboard endpoint
@api_router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard_stats():
    # Get room statistics
    total_rooms = await db.rooms.count_documents({})
    available_rooms = await db.rooms.count_documents({"status": RoomStatus.AVAILABLE})
    occupied_rooms = await db.rooms.count_documents({"status": RoomStatus.OCCUPIED})
    maintenance_rooms = await db.rooms.count_documents({"status": RoomStatus.MAINTENANCE})
    cleaning_rooms = await db.rooms.count_documents({"status": RoomStatus.CLEANING})
    
    # Get today's check-ins and check-outs
    today = date.today()
    today_str = today.isoformat()  # Convert date to string for MongoDB
    
    today_checkins = await db.bookings.count_documents({
        "check_in_date": today_str,
        "status": {"$in": [BookingStatus.CONFIRMED, BookingStatus.CHECKED_IN]}
    })
    today_checkouts = await db.bookings.count_documents({
        "check_out_date": today_str,
        "status": BookingStatus.CHECKED_OUT
    })
    
    # Calculate total revenue (completed bookings)
    completed_bookings = await db.bookings.find({
        "status": BookingStatus.CHECKED_OUT
    }).to_list(1000)
    total_revenue = sum(booking["total_amount"] for booking in completed_bookings)
    
    return DashboardStats(
        total_rooms=total_rooms,
        available_rooms=available_rooms,
        occupied_rooms=occupied_rooms,
        maintenance_rooms=maintenance_rooms,
        cleaning_rooms=cleaning_rooms,
        today_checkins=today_checkins,
        today_checkouts=today_checkouts,
        total_revenue=total_revenue
    )

# Room availability check
@api_router.get("/rooms/{room_id}/availability")
async def check_room_availability_endpoint(room_id: str, check_in: date, check_out: date):
    room = await db.rooms.find_one({"id": room_id})
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    # Convert date objects to strings for MongoDB
    check_in_str = check_in.isoformat() if isinstance(check_in, date) else check_in
    check_out_str = check_out.isoformat() if isinstance(check_out, date) else check_out
    
    is_available = await check_room_availability(room_id, check_in_str, check_out_str)
    return {"available": is_available}

# Get bookings for a specific date range
@api_router.get("/bookings/range")
async def get_bookings_by_date_range(start_date: date, end_date: date):
    # Convert date objects to strings for MongoDB
    start_date_str = start_date.isoformat() if isinstance(start_date, date) else start_date
    end_date_str = end_date.isoformat() if isinstance(end_date, date) else end_date
    
    bookings = await db.bookings.find({
        "$or": [
            {"check_in_date": {"$gte": start_date_str, "$lte": end_date_str}},
            {"check_out_date": {"$gte": start_date_str, "$lte": end_date_str}},
            {"check_in_date": {"$lte": start_date_str}, "check_out_date": {"$gte": end_date_str}}
        ]
    }).to_list(100)
    
    # Convert string dates back to date objects for response
    for booking in bookings:
        if 'check_in_date' in booking and isinstance(booking['check_in_date'], str):
            booking['check_in_date'] = date.fromisoformat(booking['check_in_date'])
        if 'check_out_date' in booking and isinstance(booking['check_out_date'], str):
            booking['check_out_date'] = date.fromisoformat(booking['check_out_date'])
    
    return [Booking(**booking) for booking in bookings]

# Payment endpoints
@api_router.post("/payments", response_model=Payment)
async def create_payment(payment: PaymentCreate):
    # Validate booking exists
    booking = await db.bookings.find_one({"id": payment.booking_id})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    payment_dict = payment.dict()
    payment_obj = Payment(**payment_dict)
    await db.payments.insert_one(payment_obj.dict())
    return payment_obj

@api_router.get("/payments", response_model=List[Payment])
async def get_payments():
    payments = await db.payments.find().to_list(100)
    return [Payment(**payment) for payment in payments]

@api_router.get("/payments/booking/{booking_id}", response_model=List[Payment])
async def get_payments_by_booking(booking_id: str):
    payments = await db.payments.find({"booking_id": booking_id}).to_list(100)
    return [Payment(**payment) for payment in payments]

@api_router.get("/bookings/{booking_id}/balance")
async def get_booking_balance(booking_id: str):
    booking = await db.bookings.find_one({"id": booking_id})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    # Calculate total payments
    payments = await db.payments.find({"booking_id": booking_id}).to_list(100)
    total_paid = sum(payment["amount"] for payment in payments)
    
    balance = booking["total_amount"] - total_paid
    
    return {
        "booking_id": booking_id,
        "total_amount": booking["total_amount"],
        "total_paid": total_paid,
        "balance_due": balance,
        "payments": [Payment(**payment) for payment in payments]
    }

# Expense endpoints
@api_router.post("/expenses", response_model=Expense)
async def create_expense(expense: ExpenseCreate):
    expense_dict = expense.dict()
    if expense_dict.get("expense_date") is None:
        expense_dict["expense_date"] = date.today()
    
    expense_obj = Expense(**expense_dict)
    
    # Convert date to string for MongoDB
    expense_data = expense_obj.dict()
    if isinstance(expense_data["expense_date"], date):
        expense_data["expense_date"] = expense_data["expense_date"].isoformat()
    
    await db.expenses.insert_one(expense_data)
    return expense_obj

@api_router.get("/expenses", response_model=List[Expense])
async def get_expenses():
    expenses = await db.expenses.find().to_list(100)
    # Convert date strings back to date objects
    for expense in expenses:
        if isinstance(expense["expense_date"], str):
            expense["expense_date"] = date.fromisoformat(expense["expense_date"])
    return [Expense(**expense) for expense in expenses]

@api_router.get("/expenses/{expense_id}", response_model=Expense)
async def get_expense(expense_id: str):
    expense = await db.expenses.find_one({"id": expense_id})
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    
    if isinstance(expense["expense_date"], str):
        expense["expense_date"] = date.fromisoformat(expense["expense_date"])
    
    return Expense(**expense)

@api_router.put("/expenses/{expense_id}", response_model=Expense)
async def update_expense(expense_id: str, expense_update: ExpenseCreate):
    expense = await db.expenses.find_one({"id": expense_id})
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    
    update_data = expense_update.dict()
    if update_data.get("expense_date") and isinstance(update_data["expense_date"], date):
        update_data["expense_date"] = update_data["expense_date"].isoformat()
    
    await db.expenses.update_one({"id": expense_id}, {"$set": update_data})
    
    updated_expense = await db.expenses.find_one({"id": expense_id})
    if isinstance(updated_expense["expense_date"], str):
        updated_expense["expense_date"] = date.fromisoformat(updated_expense["expense_date"])
    
    return Expense(**updated_expense)

@api_router.delete("/expenses/{expense_id}")
async def delete_expense(expense_id: str):
    expense = await db.expenses.find_one({"id": expense_id})
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    
    await db.expenses.delete_one({"id": expense_id})
    return {"message": "Expense deleted successfully"}

# Invoice generation
@api_router.post("/invoices/generate/{booking_id}")
async def generate_invoice(booking_id: str):
    # Get booking details
    booking = await db.bookings.find_one({"id": booking_id})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    # Get guest details
    guest = await db.guests.find_one({"id": booking["guest_id"]})
    if not guest:
        raise HTTPException(status_code=404, detail="Guest not found")
    
    # Get room details
    room = await db.rooms.find_one({"id": booking["room_id"]})
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    # Get payments
    payments = await db.payments.find({"booking_id": booking_id}).to_list(100)
    total_paid = sum(payment["amount"] for payment in payments)
    
    # Create invoice
    invoice_data = {
        "booking_id": booking_id,
        "guest_name": guest["name"],
        "room_number": room["room_number"],
        "check_in_date": booking["check_in_date"],
        "check_out_date": booking["check_out_date"],
        "total_amount": booking["total_amount"],
        "advance_paid": sum(p["amount"] for p in payments if p.get("is_advance", False)),
        "balance_due": booking["total_amount"] - total_paid,
        "payments": [Payment(**payment) for payment in payments]
    }
    
    if isinstance(invoice_data["check_in_date"], str):
        invoice_data["check_in_date"] = date.fromisoformat(invoice_data["check_in_date"])
    if isinstance(invoice_data["check_out_date"], str):
        invoice_data["check_out_date"] = date.fromisoformat(invoice_data["check_out_date"])
    
    invoice_obj = Invoice(**invoice_data)
    
    # Save invoice to database
    invoice_dict = invoice_obj.dict()
    if isinstance(invoice_dict["check_in_date"], date):
        invoice_dict["check_in_date"] = invoice_dict["check_in_date"].isoformat()
    if isinstance(invoice_dict["check_out_date"], date):
        invoice_dict["check_out_date"] = invoice_dict["check_out_date"].isoformat()
    
    await db.invoices.insert_one(invoice_dict)
    return invoice_obj

@api_router.get("/invoices/{invoice_id}/pdf")
async def download_invoice_pdf(invoice_id: str):
    invoice = await db.invoices.find_one({"id": invoice_id})
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Convert date strings back to date objects
    if isinstance(invoice["check_in_date"], str):
        invoice["check_in_date"] = date.fromisoformat(invoice["check_in_date"])
    if isinstance(invoice["check_out_date"], str):
        invoice["check_out_date"] = date.fromisoformat(invoice["check_out_date"])
    
    # Generate PDF
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        alignment=TA_CENTER
    )
    story.append(Paragraph("HOTEL INVOICE", title_style))
    
    # Invoice details
    story.append(Paragraph(f"<b>Invoice ID:</b> {invoice['id']}", styles['Normal']))
    story.append(Paragraph(f"<b>Guest Name:</b> {invoice['guest_name']}", styles['Normal']))
    story.append(Paragraph(f"<b>Room Number:</b> {invoice['room_number']}", styles['Normal']))
    story.append(Paragraph(f"<b>Check-in Date:</b> {invoice['check_in_date']}", styles['Normal']))
    story.append(Paragraph(f"<b>Check-out Date:</b> {invoice['check_out_date']}", styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Payment details table
    data = [
        ['Description', 'Amount'],
        ['Total Amount', f"${invoice['total_amount']:.2f}"],
        ['Advance Paid', f"${invoice['advance_paid']:.2f}"],
        ['Balance Due', f"${invoice['balance_due']:.2f}"]
    ]
    
    table = Table(data, colWidths=[3*inch, 2*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(table)
    story.append(Spacer(1, 20))
    
    # Payment history
    if invoice.get('payments'):
        story.append(Paragraph("<b>Payment History:</b>", styles['Normal']))
        payment_data = [['Date', 'Type', 'Amount', 'Description']]
        for payment in invoice['payments']:
            payment_data.append([
                payment.get('payment_date', 'N/A'),
                payment.get('payment_type', 'N/A'),
                f"${payment.get('amount', 0):.2f}",
                payment.get('description', 'N/A')
            ])
        
        payment_table = Table(payment_data, colWidths=[1.5*inch, 1*inch, 1*inch, 2.5*inch])
        payment_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(payment_table)
    
    doc.build(story)
    buffer.seek(0)
    
    return StreamingResponse(
        io.BytesIO(buffer.read()),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=invoice_{invoice_id}.pdf"}
    )

# Financial reporting
@api_router.get("/financial/report", response_model=FinancialReport)
async def get_financial_report(report_date: date):
    # Get bookings for the date
    report_date_str = report_date.isoformat()
    
    # Get completed bookings for the date
    completed_bookings = await db.bookings.find({
        "status": BookingStatus.CHECKED_OUT,
        "check_out_date": report_date_str
    }).to_list(100)
    
    # Get payments for the date
    payments = await db.payments.find({
        "payment_date": {
            "$gte": datetime.combine(report_date, datetime.min.time()),
            "$lt": datetime.combine(report_date, datetime.max.time())
        }
    }).to_list(100)
    
    # Get expenses for the date
    expenses = await db.expenses.find({
        "expense_date": report_date_str
    }).to_list(100)
    
    # Calculate totals
    total_income = sum(payment["amount"] for payment in payments)
    total_expenses = sum(expense["amount"] for expense in expenses)
    net_profit = total_income - total_expenses
    
    room_revenue = sum(booking["total_amount"] for booking in completed_bookings)
    advance_payments = sum(payment["amount"] for payment in payments if payment.get("is_advance", False))
    final_payments = sum(payment["amount"] for payment in payments if not payment.get("is_advance", False))
    
    # Group expenses by category
    expenses_by_category = {}
    for expense in expenses:
        category = expense["category"]
        if category not in expenses_by_category:
            expenses_by_category[category] = 0
        expenses_by_category[category] += expense["amount"]
    
    return FinancialReport(
        date=report_date,
        total_income=total_income,
        total_expenses=total_expenses,
        net_profit=net_profit,
        total_bookings=len(completed_bookings),
        room_revenue=room_revenue,
        advance_payments=advance_payments,
        final_payments=final_payments,
        expenses_by_category=expenses_by_category
    )

@api_router.get("/financial/report/pdf")
async def download_financial_report_pdf(report_date: date):
    # Get financial report data
    report = await get_financial_report(report_date)
    
    # Generate PDF
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        alignment=TA_CENTER
    )
    story.append(Paragraph(f"DAILY FINANCIAL REPORT - {report_date}", title_style))
    
    # Summary table
    summary_data = [
        ['Metric', 'Amount'],
        ['Total Income', f"${report.total_income:.2f}"],
        ['Total Expenses', f"${report.total_expenses:.2f}"],
        ['Net Profit', f"${report.net_profit:.2f}"],
        ['Total Bookings', str(report.total_bookings)],
        ['Room Revenue', f"${report.room_revenue:.2f}"],
        ['Advance Payments', f"${report.advance_payments:.2f}"],
        ['Final Payments', f"${report.final_payments:.2f}"]
    ]
    
    table = Table(summary_data, colWidths=[3*inch, 2*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(table)
    story.append(Spacer(1, 20))
    
    # Expenses by category
    if report.expenses_by_category:
        story.append(Paragraph("<b>Expenses by Category:</b>", styles['Normal']))
        expense_data = [['Category', 'Amount']]
        for category, amount in report.expenses_by_category.items():
            expense_data.append([category.title(), f"${amount:.2f}"])
        
        expense_table = Table(expense_data, colWidths=[3*inch, 2*inch])
        expense_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(expense_table)
    
    doc.build(story)
    buffer.seek(0)
    
    return StreamingResponse(
        io.BytesIO(buffer.read()),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=financial_report_{report_date}.pdf"}
    )

# Enhanced booking checkout
@api_router.post("/bookings/{booking_id}/checkout")
async def checkout_booking(booking_id: str, final_payment: Optional[PaymentCreate] = None):
    booking = await db.bookings.find_one({"id": booking_id})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    if booking["status"] != BookingStatus.CHECKED_IN:
        raise HTTPException(status_code=400, detail="Booking must be checked in to checkout")
    
    # Calculate balance
    payments = await db.payments.find({"booking_id": booking_id}).to_list(100)
    total_paid = sum(payment["amount"] for payment in payments)
    balance_due = booking["total_amount"] - total_paid
    
    # If there's a final payment, process it
    if final_payment and balance_due > 0:
        if final_payment.amount > balance_due:
            raise HTTPException(status_code=400, detail="Payment amount exceeds balance due")
        
        final_payment_dict = final_payment.dict()
        final_payment_dict["booking_id"] = booking_id
        final_payment_dict["is_advance"] = False
        final_payment_obj = Payment(**final_payment_dict)
        await db.payments.insert_one(final_payment_obj.dict())
        
        total_paid += final_payment.amount
        balance_due -= final_payment.amount
    
    # Update booking status
    await db.bookings.update_one(
        {"id": booking_id}, 
        {"$set": {"status": BookingStatus.CHECKED_OUT}}
    )
    
    # Update room status to cleaning
    await db.rooms.update_one(
        {"id": booking["room_id"]}, 
        {"$set": {"status": RoomStatus.CLEANING}}
    )
    
    # Generate invoice
    invoice_response = await generate_invoice(booking_id)
    
    return {
        "message": "Checkout completed successfully",
        "booking_id": booking_id,
        "total_amount": booking["total_amount"],
        "total_paid": total_paid,
        "balance_due": balance_due,
        "invoice_id": invoice_response.id
    }
# Initialize default rooms
@api_router.post("/initialize-rooms")
async def initialize_default_rooms():
    # Check if rooms already exist
    existing_rooms = await db.rooms.count_documents({})
    if existing_rooms > 0:
        return {"message": "Rooms already initialized"}
    
    # Create 10 default rooms
    default_rooms = [
        {"room_number": "101", "room_type": "single", "price_per_night": 100.0, "description": "Cozy single room"},
        {"room_number": "102", "room_type": "single", "price_per_night": 100.0, "description": "Cozy single room"},
        {"room_number": "103", "room_type": "double", "price_per_night": 150.0, "description": "Comfortable double room"},
        {"room_number": "104", "room_type": "double", "price_per_night": 150.0, "description": "Comfortable double room"},
        {"room_number": "105", "room_type": "suite", "price_per_night": 250.0, "description": "Luxurious suite", "max_occupancy": 4},
        {"room_number": "201", "room_type": "single", "price_per_night": 110.0, "description": "Premium single room"},
        {"room_number": "202", "room_type": "double", "price_per_night": 160.0, "description": "Premium double room"},
        {"room_number": "203", "room_type": "deluxe", "price_per_night": 200.0, "description": "Deluxe room with city view"},
        {"room_number": "204", "room_type": "deluxe", "price_per_night": 200.0, "description": "Deluxe room with city view"},
        {"room_number": "205", "room_type": "suite", "price_per_night": 300.0, "description": "Presidential suite", "max_occupancy": 6}
    ]
    
    rooms_to_insert = []
    for room_data in default_rooms:
        room_obj = Room(**room_data)
        rooms_to_insert.append(room_obj.dict())
    
    await db.rooms.insert_many(rooms_to_insert)
    return {"message": "Successfully initialized 10 default rooms"}

# Guest search endpoint
@api_router.get("/guests/search")
async def search_guests(query: str):
    # Search guests by name, email, or phone
    guests = await db.guests.find({
        "$or": [
            {"name": {"$regex": query, "$options": "i"}},
            {"email": {"$regex": query, "$options": "i"}},
            {"phone": {"$regex": query, "$options": "i"}}
        ]
    }).to_list(10)
    return [Guest(**guest) for guest in guests]

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()