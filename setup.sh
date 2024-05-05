#!/bin/bash

echo "Installing dependencies..."
sudo apt install libffi-dev libnacl-dev python3-dev python3-venv


echo "Creating virtual environment..."
python3 -m venv venv

echo "Activating virtual environment..."
source venv/bin/activate

echo "Installing requirements..."
pip install -r requirements.txt

python3 -m pip install -U py-cord --pre

deactivate

echo "Setup complete."
echo "Run 'source venv/bin/activate' to activate the virtual environment."
