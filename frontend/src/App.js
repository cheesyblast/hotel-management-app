import React, { useState, useEffect } from 'react';
import './App.css';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Helper function to format date
const formatDate = (date) => {
  return new Date(date).toLocaleDateString();
};

// Helper function to get status color
const getStatusColor = (status) => {
  switch (status) {
    case 'available':
      return 'bg-green-100 text-green-800';
    case 'occupied':
      return 'bg-red-100 text-red-800';
    case 'maintenance':
      return 'bg-orange-100 text-orange-800';
    case 'cleaning':
      return 'bg-blue-100 text-blue-800';
    default:
      return 'bg-gray-100 text-gray-800';
  }
};

// Helper function to get booking status color
const getBookingStatusColor = (status) => {
  switch (status) {
    case 'confirmed':
      return 'bg-green-100 text-green-800';
    case 'checked_in':
      return 'bg-blue-100 text-blue-800';
    case 'checked_out':
      return 'bg-purple-100 text-purple-800';
    case 'cancelled':
      return 'bg-red-100 text-red-800';
    case 'pending':
      return 'bg-yellow-100 text-yellow-800';
    default:
      return 'bg-gray-100 text-gray-800';
  }
};

// Dashboard Component
const Dashboard = ({ stats, onRefresh }) => {
  return (
    <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-2xl font-bold text-gray-800">Hotel Dashboard</h2>
        <button
          onClick={onRefresh}
          className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg transition-colors"
        >
          Refresh
        </button>
      </div>
      
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-blue-50 p-4 rounded-lg">
          <h3 className="text-sm font-medium text-blue-600">Total Rooms</h3>
          <p className="text-2xl font-bold text-blue-800">{stats.total_rooms}</p>
        </div>
        <div className="bg-green-50 p-4 rounded-lg">
          <h3 className="text-sm font-medium text-green-600">Available</h3>
          <p className="text-2xl font-bold text-green-800">{stats.available_rooms}</p>
        </div>
        <div className="bg-red-50 p-4 rounded-lg">
          <h3 className="text-sm font-medium text-red-600">Occupied</h3>
          <p className="text-2xl font-bold text-red-800">{stats.occupied_rooms}</p>
        </div>
        <div className="bg-purple-50 p-4 rounded-lg">
          <h3 className="text-sm font-medium text-purple-600">Revenue</h3>
          <p className="text-2xl font-bold text-purple-800">${stats.total_revenue}</p>
        </div>
      </div>
      
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
        <div className="bg-orange-50 p-4 rounded-lg">
          <h3 className="text-sm font-medium text-orange-600">Maintenance</h3>
          <p className="text-2xl font-bold text-orange-800">{stats.maintenance_rooms}</p>
        </div>
        <div className="bg-cyan-50 p-4 rounded-lg">
          <h3 className="text-sm font-medium text-cyan-600">Cleaning</h3>
          <p className="text-2xl font-bold text-cyan-800">{stats.cleaning_rooms}</p>
        </div>
        <div className="bg-indigo-50 p-4 rounded-lg">
          <h3 className="text-sm font-medium text-indigo-600">Today Check-ins</h3>
          <p className="text-2xl font-bold text-indigo-800">{stats.today_checkins}</p>
        </div>
        <div className="bg-pink-50 p-4 rounded-lg">
          <h3 className="text-sm font-medium text-pink-600">Today Check-outs</h3>
          <p className="text-2xl font-bold text-pink-800">{stats.today_checkouts}</p>
        </div>
      </div>
    </div>
  );
};

// Rooms Grid Component
const RoomsGrid = ({ rooms, onRoomClick, onStatusChange }) => {
  return (
    <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
      <h2 className="text-2xl font-bold text-gray-800 mb-4">Room Status</h2>
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        {rooms.map((room) => (
          <div
            key={room.id}
            className="border-2 border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer"
            onClick={() => onRoomClick(room)}
          >
            <div className="flex justify-between items-start mb-2">
              <h3 className="text-lg font-semibold text-gray-800">{room.room_number}</h3>
              <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(room.status)}`}>
                {room.status}
              </span>
            </div>
            <p className="text-sm text-gray-600 mb-1">{room.room_type}</p>
            <p className="text-sm font-medium text-gray-800">${room.price_per_night}/night</p>
            <div className="mt-2">
              <select
                className="w-full text-xs border rounded px-2 py-1"
                value={room.status}
                onChange={(e) => onStatusChange(room.id, e.target.value)}
                onClick={(e) => e.stopPropagation()}
              >
                <option value="available">Available</option>
                <option value="occupied">Occupied</option>
                <option value="maintenance">Maintenance</option>
                <option value="cleaning">Cleaning</option>
              </select>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

// Booking Form Component
const BookingForm = ({ guests, rooms, onSubmit, onCancel }) => {
  const [formData, setFormData] = useState({
    guest_id: '',
    room_id: '',
    check_in_date: '',
    check_out_date: '',
    special_requests: ''
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(formData);
  };

  const availableRooms = rooms.filter(room => room.status === 'available');

  return (
    <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
      <h2 className="text-2xl font-bold text-gray-800 mb-4">Create New Booking</h2>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Guest</label>
          <select
            className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            value={formData.guest_id}
            onChange={(e) => setFormData({...formData, guest_id: e.target.value})}
            required
          >
            <option value="">Select Guest</option>
            {guests.map(guest => (
              <option key={guest.id} value={guest.id}>{guest.name} - {guest.email}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Room</label>
          <select
            className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            value={formData.room_id}
            onChange={(e) => setFormData({...formData, room_id: e.target.value})}
            required
          >
            <option value="">Select Room</option>
            {availableRooms.map(room => (
              <option key={room.id} value={room.id}>
                {room.room_number} - {room.room_type} - ${room.price_per_night}/night
              </option>
            ))}
          </select>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Check-in Date</label>
            <input
              type="date"
              className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={formData.check_in_date}
              onChange={(e) => setFormData({...formData, check_in_date: e.target.value})}
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Check-out Date</label>
            <input
              type="date"
              className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={formData.check_out_date}
              onChange={(e) => setFormData({...formData, check_out_date: e.target.value})}
              required
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Special Requests</label>
          <textarea
            className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            rows="3"
            value={formData.special_requests}
            onChange={(e) => setFormData({...formData, special_requests: e.target.value})}
            placeholder="Any special requests or notes..."
          />
        </div>

        <div className="flex space-x-4">
          <button
            type="submit"
            className="bg-blue-500 hover:bg-blue-600 text-white px-6 py-2 rounded-lg transition-colors"
          >
            Create Booking
          </button>
          <button
            type="button"
            onClick={onCancel}
            className="bg-gray-500 hover:bg-gray-600 text-white px-6 py-2 rounded-lg transition-colors"
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
};

// Bookings List Component
const BookingsList = ({ bookings, guests, rooms, onStatusChange }) => {
  const getGuestName = (guestId) => {
    const guest = guests.find(g => g.id === guestId);
    return guest ? guest.name : 'Unknown Guest';
  };

  const getRoomNumber = (roomId) => {
    const room = rooms.find(r => r.id === roomId);
    return room ? room.room_number : 'Unknown Room';
  };

  return (
    <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
      <h2 className="text-2xl font-bold text-gray-800 mb-4">Current Bookings</h2>
      <div className="space-y-4">
        {bookings.map((booking) => (
          <div key={booking.id} className="border border-gray-200 rounded-lg p-4">
            <div className="flex justify-between items-start mb-2">
              <div>
                <h3 className="text-lg font-semibold text-gray-800">
                  {getGuestName(booking.guest_id)} - Room {getRoomNumber(booking.room_id)}
                </h3>
                <p className="text-sm text-gray-600">
                  {formatDate(booking.check_in_date)} to {formatDate(booking.check_out_date)}
                </p>
              </div>
              <span className={`px-3 py-1 rounded-full text-sm font-medium ${getBookingStatusColor(booking.status)}`}>
                {booking.status.replace('_', ' ')}
              </span>
            </div>
            <p className="text-sm text-gray-600 mb-2">Total: ${booking.total_amount}</p>
            {booking.special_requests && (
              <p className="text-sm text-gray-600 mb-2">
                <strong>Special Requests:</strong> {booking.special_requests}
              </p>
            )}
            <div className="flex space-x-2">
              <select
                className="text-sm border rounded px-2 py-1"
                value={booking.status}
                onChange={(e) => onStatusChange(booking.id, e.target.value)}
              >
                <option value="pending">Pending</option>
                <option value="confirmed">Confirmed</option>
                <option value="checked_in">Checked In</option>
                <option value="checked_out">Checked Out</option>
                <option value="cancelled">Cancelled</option>
              </select>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

// Guest Form Component
const GuestForm = ({ onSubmit, onCancel }) => {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    phone: '',
    address: '',
    id_number: ''
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(formData);
  };

  return (
    <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
      <h2 className="text-2xl font-bold text-gray-800 mb-4">Add New Guest</h2>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
          <input
            type="text"
            className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            value={formData.name}
            onChange={(e) => setFormData({...formData, name: e.target.value})}
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
          <input
            type="email"
            className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            value={formData.email}
            onChange={(e) => setFormData({...formData, email: e.target.value})}
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Phone</label>
          <input
            type="tel"
            className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            value={formData.phone}
            onChange={(e) => setFormData({...formData, phone: e.target.value})}
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Address</label>
          <input
            type="text"
            className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            value={formData.address}
            onChange={(e) => setFormData({...formData, address: e.target.value})}
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">ID Number</label>
          <input
            type="text"
            className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            value={formData.id_number}
            onChange={(e) => setFormData({...formData, id_number: e.target.value})}
          />
        </div>

        <div className="flex space-x-4">
          <button
            type="submit"
            className="bg-blue-500 hover:bg-blue-600 text-white px-6 py-2 rounded-lg transition-colors"
          >
            Add Guest
          </button>
          <button
            type="button"
            onClick={onCancel}
            className="bg-gray-500 hover:bg-gray-600 text-white px-6 py-2 rounded-lg transition-colors"
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
};

// Main App Component
function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [stats, setStats] = useState({});
  const [rooms, setRooms] = useState([]);
  const [guests, setGuests] = useState([]);
  const [bookings, setBookings] = useState([]);
  const [showBookingForm, setShowBookingForm] = useState(false);
  const [showGuestForm, setShowGuestForm] = useState(false);
  const [selectedRoom, setSelectedRoom] = useState(null);
  const [loading, setLoading] = useState(true);

  // Initialize default rooms
  const initializeRooms = async () => {
    try {
      await axios.post(`${API}/initialize-rooms`);
      loadData();
    } catch (error) {
      console.error('Error initializing rooms:', error);
    }
  };

  // Load all data
  const loadData = async () => {
    try {
      setLoading(true);
      const [statsRes, roomsRes, guestsRes, bookingsRes] = await Promise.all([
        axios.get(`${API}/dashboard`),
        axios.get(`${API}/rooms`),
        axios.get(`${API}/guests`),
        axios.get(`${API}/bookings`)
      ]);

      setStats(statsRes.data);
      setRooms(roomsRes.data);
      setGuests(guestsRes.data);
      setBookings(bookingsRes.data);
    } catch (error) {
      console.error('Error loading data:', error);
      // Initialize rooms if none exist
      if (error.response?.status === 404) {
        await initializeRooms();
      }
    } finally {
      setLoading(false);
    }
  };

  // Update room status
  const updateRoomStatus = async (roomId, status) => {
    try {
      await axios.put(`${API}/rooms/${roomId}`, { status });
      loadData();
    } catch (error) {
      console.error('Error updating room status:', error);
    }
  };

  // Create booking
  const createBooking = async (bookingData) => {
    try {
      await axios.post(`${API}/bookings`, bookingData);
      setShowBookingForm(false);
      loadData();
    } catch (error) {
      console.error('Error creating booking:', error);
      alert('Error creating booking: ' + (error.response?.data?.detail || error.message));
    }
  };

  // Create guest
  const createGuest = async (guestData) => {
    try {
      await axios.post(`${API}/guests`, guestData);
      setShowGuestForm(false);
      loadData();
    } catch (error) {
      console.error('Error creating guest:', error);
      alert('Error creating guest: ' + (error.response?.data?.detail || error.message));
    }
  };

  // Update booking status
  const updateBookingStatus = async (bookingId, status) => {
    try {
      await axios.put(`${API}/bookings/${bookingId}`, { status });
      loadData();
    } catch (error) {
      console.error('Error updating booking status:', error);
    }
  };

  // Load data on component mount
  useEffect(() => {
    loadData();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading hotel management system...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100">
      <div className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <h1 className="text-3xl font-bold text-gray-900">Hotel Management System</h1>
            <nav className="flex space-x-4">
              <button
                onClick={() => setActiveTab('dashboard')}
                className={`px-4 py-2 rounded-lg transition-colors ${
                  activeTab === 'dashboard'
                    ? 'bg-blue-500 text-white'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                Dashboard
              </button>
              <button
                onClick={() => setActiveTab('rooms')}
                className={`px-4 py-2 rounded-lg transition-colors ${
                  activeTab === 'rooms'
                    ? 'bg-blue-500 text-white'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                Rooms
              </button>
              <button
                onClick={() => setActiveTab('bookings')}
                className={`px-4 py-2 rounded-lg transition-colors ${
                  activeTab === 'bookings'
                    ? 'bg-blue-500 text-white'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                Bookings
              </button>
              <button
                onClick={() => setActiveTab('guests')}
                className={`px-4 py-2 rounded-lg transition-colors ${
                  activeTab === 'guests'
                    ? 'bg-blue-500 text-white'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                Guests
              </button>
            </nav>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {activeTab === 'dashboard' && (
          <>
            <Dashboard stats={stats} onRefresh={loadData} />
            <RoomsGrid 
              rooms={rooms} 
              onRoomClick={setSelectedRoom}
              onStatusChange={updateRoomStatus}
            />
          </>
        )}

        {activeTab === 'rooms' && (
          <RoomsGrid 
            rooms={rooms} 
            onRoomClick={setSelectedRoom}
            onStatusChange={updateRoomStatus}
          />
        )}

        {activeTab === 'bookings' && (
          <>
            <div className="mb-4">
              <button
                onClick={() => setShowBookingForm(!showBookingForm)}
                className="bg-blue-500 hover:bg-blue-600 text-white px-6 py-2 rounded-lg transition-colors"
              >
                {showBookingForm ? 'Cancel' : 'New Booking'}
              </button>
            </div>
            
            {showBookingForm && (
              <BookingForm 
                guests={guests}
                rooms={rooms}
                onSubmit={createBooking}
                onCancel={() => setShowBookingForm(false)}
              />
            )}
            
            <BookingsList 
              bookings={bookings}
              guests={guests}
              rooms={rooms}
              onStatusChange={updateBookingStatus}
            />
          </>
        )}

        {activeTab === 'guests' && (
          <>
            <div className="mb-4">
              <button
                onClick={() => setShowGuestForm(!showGuestForm)}
                className="bg-blue-500 hover:bg-blue-600 text-white px-6 py-2 rounded-lg transition-colors"
              >
                {showGuestForm ? 'Cancel' : 'Add Guest'}
              </button>
            </div>
            
            {showGuestForm && (
              <GuestForm 
                onSubmit={createGuest}
                onCancel={() => setShowGuestForm(false)}
              />
            )}
            
            <div className="bg-white rounded-lg shadow-lg p-6">
              <h2 className="text-2xl font-bold text-gray-800 mb-4">Guest List</h2>
              <div className="space-y-4">
                {guests.map((guest) => (
                  <div key={guest.id} className="border border-gray-200 rounded-lg p-4">
                    <h3 className="text-lg font-semibold text-gray-800">{guest.name}</h3>
                    <p className="text-sm text-gray-600">{guest.email}</p>
                    <p className="text-sm text-gray-600">{guest.phone}</p>
                    {guest.address && (
                      <p className="text-sm text-gray-600">{guest.address}</p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

export default App;