#!/bin/bash

# Check if MySQL client is installed
if ! command -v mysql &> /dev/null; then
    echo "MySQL client is not installed. Please install it first."
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Creating .env file..."
    cat > .env << EOF
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_password_here
DB_NAME=bifrost_db
EOF
    echo ".env file created. Please update with your database credentials."
else
    echo ".env file already exists."
fi

# Source the .env file to get database credentials
source .env

# Run the migrations.sql file to create database and tables
echo "Setting up database..."
if [ "$DB_USER" = "root" ]; then
    # For root user, use sudo
    echo "Using sudo for root MySQL user..."
    sudo mysql < migrations.sql
else
    # For non-root users
    if [ -z "$DB_PASSWORD" ]; then
        # If password is empty
        mysql -h "$DB_HOST" -u "$DB_USER" < migrations.sql
    else
        # If password is set
        mysql -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASSWORD" < migrations.sql
    fi
fi

# Check if database setup was successful
if [ $? -eq 0 ]; then
    echo "Database setup completed successfully."
    echo "You can now start the server with: npm start"
else
    echo "Database setup failed. Please check your credentials and try again."
    exit 1
fi
