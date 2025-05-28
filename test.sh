#!/bin/bash

# Exit on errors
set -e

# Start servers in background and capture their PIDs
echo "Starting backend server on port 8080..."
python3 -m http.server 8080 --directory backend/src > backend.log 2>&1 &
PID1=$!

echo "Starting frontend server on port 8081..."
python3 -m http.server 8081 --directory frontend/src > frontend.log 2>&1 &
PID2=$!

echo "Starting frontend client server on port 8082..."
python3 -m http.server 8082 --directory frontend_client/src > frontend_client.log 2>&1 &
PID3=$!

echo "All servers started:"
echo "  Backend:          http://localhost:8080"
echo "  Frontend:         http://localhost:8081"
echo "  Frontend Client:  http://localhost:8082"
echo "Press [Enter] to stop all servers..."

# Wait for user input
read

# Kill all servers
echo "Stopping servers..."
kill $PID1 $PID2 $PID3

echo "All servers stopped."

