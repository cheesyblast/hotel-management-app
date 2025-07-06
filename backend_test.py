import requests
import json
from datetime import datetime, timedelta
import uuid
import time

# Get the backend URL from the frontend .env file
with open('/app/frontend/.env', 'r') as f:
    for line in f:
        if line.startswith('REACT_APP_BACKEND_URL='):
            BACKEND_URL = line.strip().split('=')[1].strip('"\'')
            break

# Ensure the URL doesn't have quotes
BACKEND_URL = BACKEND_URL.strip('"\'')
API_URL = f"{BACKEND_URL}/api"

print(f"Testing backend API at: {API_URL}")

# Test data
test_room = {
    "room_number": "999",
    "room_type": "suite",
    "price_per_night": 250.0,
    "description": "Test suite room",
    "max_occupancy": 4,
    "amenities": ["TV", "Mini Bar", "Balcony"]
}

test_guest = {
    "name": "John Doe",
    "email": "john.doe@example.com",
    "phone": "123-456-7890",
    "address": "123 Test Street, Test City",
    "id_number": "AB123456"
}

# Helper functions
def print_test_result(test_name, success, response=None, error=None):
    if success:
        print(f"✅ {test_name}: PASSED")
        if response:
            print(f"   Response: {response}")
    else:
        print(f"❌ {test_name}: FAILED")
        if error:
            print(f"   Error: {error}")
        if response:
            print(f"   Response: {response}")
    print("-" * 80)

def format_date(date_obj):
    return date_obj.strftime("%Y-%m-%d")

# Test functions
def test_initialize_rooms():
    try:
        response = requests.post(f"{API_URL}/initialize-rooms")
        response.raise_for_status()
        data = response.json()
        print_test_result("Initialize Rooms", True, data)
        return True
    except Exception as e:
        print_test_result("Initialize Rooms", False, error=str(e))
        return False

def test_get_dashboard():
    try:
        response = requests.get(f"{API_URL}/dashboard")
        response.raise_for_status()
        data = response.json()
        print_test_result("Get Dashboard", True, data)
        return True
    except Exception as e:
        print_test_result("Get Dashboard", False, error=str(e))
        return False

def test_room_crud():
    # Get all rooms
    try:
        response = requests.get(f"{API_URL}/rooms")
        response.raise_for_status()
        rooms = response.json()
        print_test_result("Get All Rooms", True, f"Found {len(rooms)} rooms")
        
        # Create a new room
        response = requests.post(f"{API_URL}/rooms", json=test_room)
        response.raise_for_status()
        created_room = response.json()
        room_id = created_room["id"]
        print_test_result("Create Room", True, created_room)
        
        # Get specific room
        response = requests.get(f"{API_URL}/rooms/{room_id}")
        response.raise_for_status()
        room = response.json()
        print_test_result("Get Specific Room", True, room)
        
        # Update room
        update_data = {"price_per_night": 300.0, "status": "maintenance"}
        response = requests.put(f"{API_URL}/rooms/{room_id}", json=update_data)
        response.raise_for_status()
        updated_room = response.json()
        print_test_result("Update Room", True, updated_room)
        
        # Delete room
        response = requests.delete(f"{API_URL}/rooms/{room_id}")
        response.raise_for_status()
        delete_result = response.json()
        print_test_result("Delete Room", True, delete_result)
        
        return True
    except Exception as e:
        print_test_result("Room CRUD Operations", False, error=str(e))
        return False

def test_guest_crud():
    try:
        # Get all guests
        response = requests.get(f"{API_URL}/guests")
        response.raise_for_status()
        guests = response.json()
        print_test_result("Get All Guests", True, f"Found {len(guests)} guests")
        
        # Check if our test guest already exists
        existing_guest_id = None
        for guest in guests:
            if guest["email"] == test_guest["email"]:
                existing_guest_id = guest["id"]
                print_test_result("Test Guest Already Exists", True, f"Using existing guest with ID: {existing_guest_id}")
                break
        
        if existing_guest_id:
            guest_id = existing_guest_id
        else:
            # Create a new guest
            response = requests.post(f"{API_URL}/guests", json=test_guest)
            response.raise_for_status()
            created_guest = response.json()
            guest_id = created_guest["id"]
            print_test_result("Create Guest", True, created_guest)
        
        # Get specific guest
        response = requests.get(f"{API_URL}/guests/{guest_id}")
        response.raise_for_status()
        guest = response.json()
        print_test_result("Get Specific Guest", True, guest)
        
        # Update guest
        update_data = {"name": "John Smith", "phone": "987-654-3210", "email": guest["email"]}
        response = requests.put(f"{API_URL}/guests/{guest_id}", json=update_data)
        response.raise_for_status()
        updated_guest = response.json()
        print_test_result("Update Guest", True, updated_guest)
        
        # We won't delete the guest yet as we'll use it for booking tests
        return guest_id
    except Exception as e:
        print_test_result("Guest CRUD Operations", False, error=str(e))
        return None

def test_booking_crud(guest_id):
    try:
        # First, get a room to book
        response = requests.get(f"{API_URL}/rooms")
        response.raise_for_status()
        rooms = response.json()
        if not rooms:
            print_test_result("Booking CRUD Operations", False, error="No rooms available for booking test")
            return False
        
        room_id = rooms[0]["id"]
        
        # Get all bookings
        response = requests.get(f"{API_URL}/bookings")
        response.raise_for_status()
        bookings = response.json()
        print_test_result("Get All Bookings", True, f"Found {len(bookings)} bookings")
        
        # Create a new booking
        today = datetime.now().date()
        check_in = today + timedelta(days=1)
        check_out = today + timedelta(days=3)
        
        booking_data = {
            "guest_id": guest_id,
            "room_id": room_id,
            "check_in_date": format_date(check_in),
            "check_out_date": format_date(check_out),
            "special_requests": "Extra pillows please"
        }
        
        response = requests.post(f"{API_URL}/bookings", json=booking_data)
        response.raise_for_status()
        created_booking = response.json()
        booking_id = created_booking["id"]
        print_test_result("Create Booking", True, created_booking)
        
        # Get specific booking
        response = requests.get(f"{API_URL}/bookings/{booking_id}")
        response.raise_for_status()
        booking = response.json()
        print_test_result("Get Specific Booking", True, booking)
        
        # Update booking status to CONFIRMED
        update_data = {"status": "confirmed"}
        response = requests.put(f"{API_URL}/bookings/{booking_id}", json=update_data)
        response.raise_for_status()
        updated_booking = response.json()
        print_test_result("Update Booking to CONFIRMED", True, updated_booking)
        
        # Check if room status is updated
        response = requests.get(f"{API_URL}/rooms/{room_id}")
        response.raise_for_status()
        room = response.json()
        print_test_result("Room Status After Confirmation", True, f"Room status: {room['status']}")
        
        # Update booking status to CHECKED_IN
        update_data = {"status": "checked_in"}
        response = requests.put(f"{API_URL}/bookings/{booking_id}", json=update_data)
        response.raise_for_status()
        updated_booking = response.json()
        print_test_result("Update Booking to CHECKED_IN", True, updated_booking)
        
        # Check if room status is updated to OCCUPIED
        response = requests.get(f"{API_URL}/rooms/{room_id}")
        response.raise_for_status()
        room = response.json()
        print_test_result("Room Status After Check-in", True, f"Room status: {room['status']}")
        
        # Update booking status to CHECKED_OUT
        update_data = {"status": "checked_out"}
        response = requests.put(f"{API_URL}/bookings/{booking_id}", json=update_data)
        response.raise_for_status()
        updated_booking = response.json()
        print_test_result("Update Booking to CHECKED_OUT", True, updated_booking)
        
        # Check if room status is updated to CLEANING
        response = requests.get(f"{API_URL}/rooms/{room_id}")
        response.raise_for_status()
        room = response.json()
        print_test_result("Room Status After Check-out", True, f"Room status: {room['status']}")
        
        # Delete booking
        response = requests.delete(f"{API_URL}/bookings/{booking_id}")
        response.raise_for_status()
        delete_result = response.json()
        print_test_result("Delete Booking", True, delete_result)
        
        return True
    except Exception as e:
        print_test_result("Booking CRUD Operations", False, error=str(e))
        return False

def test_booking_conflict_detection(guest_id):
    try:
        # First, get a room to book
        response = requests.get(f"{API_URL}/rooms")
        response.raise_for_status()
        rooms = response.json()
        if not rooms:
            print_test_result("Booking Conflict Detection", False, error="No rooms available for booking test")
            return False
        
        room_id = rooms[0]["id"]
        
        # Create a booking
        today = datetime.now().date()
        check_in = today + timedelta(days=5)
        check_out = today + timedelta(days=7)
        
        booking_data = {
            "guest_id": guest_id,
            "room_id": room_id,
            "check_in_date": format_date(check_in),
            "check_out_date": format_date(check_out),
            "special_requests": "Test booking for conflict detection"
        }
        
        response = requests.post(f"{API_URL}/bookings", json=booking_data)
        response.raise_for_status()
        created_booking = response.json()
        booking_id = created_booking["id"]
        print_test_result("Create First Booking", True, created_booking)
        
        # Update booking status to CONFIRMED
        update_data = {"status": "confirmed"}
        response = requests.put(f"{API_URL}/bookings/{booking_id}", json=update_data)
        response.raise_for_status()
        
        # Try to create an overlapping booking
        overlapping_booking_data = {
            "guest_id": guest_id,
            "room_id": room_id,
            "check_in_date": format_date(check_in + timedelta(days=1)),
            "check_out_date": format_date(check_out + timedelta(days=1)),
            "special_requests": "This should fail due to conflict"
        }
        
        try:
            response = requests.post(f"{API_URL}/bookings", json=overlapping_booking_data)
            response.raise_for_status()
            print_test_result("Booking Conflict Detection", False, "Created overlapping booking when it should have failed")
            
            # Clean up the successful but incorrect booking
            if response.status_code == 200:
                overlap_booking_id = response.json().get("id")
                if overlap_booking_id:
                    requests.delete(f"{API_URL}/bookings/{overlap_booking_id}")
            
            # Clean up the first booking
            requests.delete(f"{API_URL}/bookings/{booking_id}")
            return False
        except requests.exceptions.HTTPError:
            # This is expected - the request should fail
            print_test_result("Booking Conflict Detection", True, "Correctly rejected overlapping booking")
            
            # Clean up the first booking
            requests.delete(f"{API_URL}/bookings/{booking_id}")
            return True
    except Exception as e:
        print_test_result("Booking Conflict Detection", False, error=str(e))
        return False

def test_room_availability_check():
    try:
        # First, get a room to check
        response = requests.get(f"{API_URL}/rooms")
        response.raise_for_status()
        rooms = response.json()
        if not rooms:
            print_test_result("Room Availability Check", False, error="No rooms available for test")
            return False
        
        room_id = rooms[0]["id"]
        
        # Check availability for future dates
        today = datetime.now().date()
        check_in = today + timedelta(days=30)
        check_out = today + timedelta(days=32)
        
        response = requests.get(
            f"{API_URL}/rooms/{room_id}/availability",
            params={"check_in": format_date(check_in), "check_out": format_date(check_out)}
        )
        response.raise_for_status()
        availability = response.json()
        print_test_result("Room Availability Check", True, availability)
        return True
    except Exception as e:
        print_test_result("Room Availability Check", False, error=str(e))
        return False

def test_date_range_validation():
    try:
        # First, get a room and guest for booking
        response = requests.get(f"{API_URL}/rooms")
        response.raise_for_status()
        rooms = response.json()
        
        response = requests.get(f"{API_URL}/guests")
        response.raise_for_status()
        guests = response.json()
        
        if not rooms or not guests:
            print_test_result("Date Range Validation", False, error="No rooms or guests available for test")
            return False
        
        room_id = rooms[0]["id"]
        guest_id = guests[0]["id"]
        
        # Try to create a booking with check-out before check-in
        today = datetime.now().date()
        check_in = today + timedelta(days=10)
        check_out = today + timedelta(days=8)  # This is before check-in
        
        invalid_booking_data = {
            "guest_id": guest_id,
            "room_id": room_id,
            "check_in_date": format_date(check_in),
            "check_out_date": format_date(check_out),
            "special_requests": "This should fail due to invalid date range"
        }
        
        try:
            response = requests.post(f"{API_URL}/bookings", json=invalid_booking_data)
            response.raise_for_status()
            print_test_result("Date Range Validation", False, "Created booking with invalid date range when it should have failed")
            
            # Clean up the successful but incorrect booking
            if response.status_code == 200:
                booking_id = response.json().get("id")
                if booking_id:
                    requests.delete(f"{API_URL}/bookings/{booking_id}")
            return False
        except requests.exceptions.HTTPError:
            # This is expected - the request should fail
            print_test_result("Date Range Validation", True, "Correctly rejected booking with invalid date range")
            return True
    except Exception as e:
        print_test_result("Date Range Validation", False, error=str(e))
        return False

def test_booking_amount_calculation():
    try:
        # First, get a room and guest for booking
        response = requests.get(f"{API_URL}/rooms")
        response.raise_for_status()
        rooms = response.json()
        
        response = requests.get(f"{API_URL}/guests")
        response.raise_for_status()
        guests = response.json()
        
        if not rooms or not guests:
            print_test_result("Booking Amount Calculation", False, error="No rooms or guests available for test")
            return False
        
        room = rooms[0]
        room_id = room["id"]
        price_per_night = room["price_per_night"]
        guest_id = guests[0]["id"]
        
        # Create a booking for 3 nights
        today = datetime.now().date()
        check_in = today + timedelta(days=20)
        check_out = today + timedelta(days=23)  # 3 nights
        
        booking_data = {
            "guest_id": guest_id,
            "room_id": room_id,
            "check_in_date": format_date(check_in),
            "check_out_date": format_date(check_out),
            "special_requests": "Test booking for amount calculation"
        }
        
        response = requests.post(f"{API_URL}/bookings", json=booking_data)
        response.raise_for_status()
        created_booking = response.json()
        booking_id = created_booking["id"]
        
        # Calculate expected amount
        expected_amount = price_per_night * 3
        actual_amount = created_booking["total_amount"]
        
        if abs(expected_amount - actual_amount) < 0.01:  # Allow for floating point precision issues
            print_test_result("Booking Amount Calculation", True, 
                             f"Expected: {expected_amount}, Actual: {actual_amount}")
            
            # Clean up
            requests.delete(f"{API_URL}/bookings/{booking_id}")
            return True
        else:
            print_test_result("Booking Amount Calculation", False, 
                             f"Expected: {expected_amount}, Actual: {actual_amount}")
            
            # Clean up
            requests.delete(f"{API_URL}/bookings/{booking_id}")
            return False
    except Exception as e:
        print_test_result("Booking Amount Calculation", False, error=str(e))
        return False

def test_edge_cases():
    try:
        # Test creating booking with non-existent guest/room
        non_existent_id = str(uuid.uuid4())
        
        # Get a valid room
        response = requests.get(f"{API_URL}/rooms")
        response.raise_for_status()
        rooms = response.json()
        if not rooms:
            print_test_result("Edge Case: Non-existent IDs", False, error="No rooms available for test")
            return False
        
        room_id = rooms[0]["id"]
        
        # Try booking with non-existent guest
        today = datetime.now().date()
        check_in = today + timedelta(days=40)
        check_out = today + timedelta(days=42)
        
        invalid_guest_booking = {
            "guest_id": non_existent_id,
            "room_id": room_id,
            "check_in_date": format_date(check_in),
            "check_out_date": format_date(check_out)
        }
        
        try:
            response = requests.post(f"{API_URL}/bookings", json=invalid_guest_booking)
            response.raise_for_status()
            print_test_result("Edge Case: Non-existent Guest", False, "Created booking with non-existent guest when it should have failed")
            return False
        except requests.exceptions.HTTPError:
            # This is expected - the request should fail
            print_test_result("Edge Case: Non-existent Guest", True, "Correctly rejected booking with non-existent guest")
        
        # Get a valid guest
        response = requests.get(f"{API_URL}/guests")
        response.raise_for_status()
        guests = response.json()
        if not guests:
            print_test_result("Edge Case: Non-existent IDs", False, error="No guests available for test")
            return False
        
        guest_id = guests[0]["id"]
        
        # Try booking with non-existent room
        invalid_room_booking = {
            "guest_id": guest_id,
            "room_id": non_existent_id,
            "check_in_date": format_date(check_in),
            "check_out_date": format_date(check_out)
        }
        
        try:
            response = requests.post(f"{API_URL}/bookings", json=invalid_room_booking)
            response.raise_for_status()
            print_test_result("Edge Case: Non-existent Room", False, "Created booking with non-existent room when it should have failed")
            return False
        except requests.exceptions.HTTPError:
            # This is expected - the request should fail
            print_test_result("Edge Case: Non-existent Room", True, "Correctly rejected booking with non-existent room")
        
        # Test deleting room with active booking
        # First create a booking
        booking_data = {
            "guest_id": guest_id,
            "room_id": room_id,
            "check_in_date": format_date(check_in),
            "check_out_date": format_date(check_out),
            "special_requests": "Test booking for delete room test"
        }
        
        response = requests.post(f"{API_URL}/bookings", json=booking_data)
        response.raise_for_status()
        created_booking = response.json()
        booking_id = created_booking["id"]
        
        # Update booking status to CONFIRMED
        update_data = {"status": "confirmed"}
        response = requests.put(f"{API_URL}/bookings/{booking_id}", json=update_data)
        response.raise_for_status()
        
        # Try to delete the room
        try:
            response = requests.delete(f"{API_URL}/rooms/{room_id}")
            response.raise_for_status()
            print_test_result("Edge Case: Delete Room with Active Booking", False, "Deleted room with active booking when it should have failed")
            
            # Clean up the booking
            requests.delete(f"{API_URL}/bookings/{booking_id}")
            return False
        except requests.exceptions.HTTPError:
            # This is expected - the request should fail
            print_test_result("Edge Case: Delete Room with Active Booking", True, "Correctly rejected deleting room with active booking")
            
            # Clean up the booking
            requests.delete(f"{API_URL}/bookings/{booking_id}")
            return True
    except Exception as e:
        print_test_result("Edge Cases", False, error=str(e))
        return False

def test_data_flow():
    try:
        # 1. Initialize rooms
        test_initialize_rooms()
        
        # 2. Create a test guest
        guest_id = test_guest_crud()
        if not guest_id:
            print_test_result("Data Flow Test", False, error="Failed to create test guest")
            return False
        
        # 3. Get dashboard stats before booking
        print("Dashboard stats before booking:")
        test_get_dashboard()
        
        # 4. Get a room to book
        response = requests.get(f"{API_URL}/rooms")
        response.raise_for_status()
        rooms = response.json()
        if not rooms:
            print_test_result("Data Flow Test", False, error="No rooms available for test")
            return False
        
        room_id = rooms[0]["id"]
        
        # 5. Create a booking
        today = datetime.now().date()
        check_in = today + timedelta(days=1)
        check_out = today + timedelta(days=3)
        
        booking_data = {
            "guest_id": guest_id,
            "room_id": room_id,
            "check_in_date": format_date(check_in),
            "check_out_date": format_date(check_out),
            "special_requests": "Data flow test booking"
        }
        
        response = requests.post(f"{API_URL}/bookings", json=booking_data)
        response.raise_for_status()
        created_booking = response.json()
        booking_id = created_booking["id"]
        print_test_result("Create Booking for Data Flow Test", True, created_booking)
        
        # 6. Test status transitions
        # PENDING -> CONFIRMED
        update_data = {"status": "confirmed"}
        response = requests.put(f"{API_URL}/bookings/{booking_id}", json=update_data)
        response.raise_for_status()
        print_test_result("Update Booking to CONFIRMED", True, response.json())
        
        # Check room status
        response = requests.get(f"{API_URL}/rooms/{room_id}")
        response.raise_for_status()
        room = response.json()
        print_test_result("Room Status After Confirmation", True, f"Room status: {room['status']}")
        
        # CONFIRMED -> CHECKED_IN
        update_data = {"status": "checked_in"}
        response = requests.put(f"{API_URL}/bookings/{booking_id}", json=update_data)
        response.raise_for_status()
        print_test_result("Update Booking to CHECKED_IN", True, response.json())
        
        # Check room status
        response = requests.get(f"{API_URL}/rooms/{room_id}")
        response.raise_for_status()
        room = response.json()
        print_test_result("Room Status After Check-in", True, f"Room status: {room['status']}")
        
        # CHECKED_IN -> CHECKED_OUT
        update_data = {"status": "checked_out"}
        response = requests.put(f"{API_URL}/bookings/{booking_id}", json=update_data)
        response.raise_for_status()
        print_test_result("Update Booking to CHECKED_OUT", True, response.json())
        
        # Check room status
        response = requests.get(f"{API_URL}/rooms/{room_id}")
        response.raise_for_status()
        room = response.json()
        print_test_result("Room Status After Check-out", True, f"Room status: {room['status']}")
        
        # 7. Get dashboard stats after booking
        print("Dashboard stats after booking:")
        test_get_dashboard()
        
        # 8. Clean up
        requests.delete(f"{API_URL}/bookings/{booking_id}")
        
        print_test_result("Data Flow Test", True, "Successfully completed data flow test")
        return True
    except Exception as e:
        print_test_result("Data Flow Test", False, error=str(e))
        return False

def run_all_tests():
    print("\n" + "=" * 80)
    print("HOTEL MANAGEMENT BACKEND API TESTS")
    print("=" * 80 + "\n")
    
    # Initialize rooms
    test_initialize_rooms()
    
    # Test dashboard
    test_get_dashboard()
    
    # Test room CRUD
    test_room_crud()
    
    # Test guest CRUD and get guest_id for booking tests
    guest_id = test_guest_crud()
    
    if guest_id:
        # Test booking CRUD
        test_booking_crud(guest_id)
        
        # Test booking conflict detection
        test_booking_conflict_detection(guest_id)
        
        # Test room availability check
        test_room_availability_check()
        
        # Test date range validation
        test_date_range_validation()
        
        # Test booking amount calculation
        test_booking_amount_calculation()
        
        # Test edge cases
        test_edge_cases()
        
        # Test data flow
        test_data_flow()
    
    print("\n" + "=" * 80)
    print("ALL TESTS COMPLETED")
    print("=" * 80 + "\n")

if __name__ == "__main__":
    run_all_tests()