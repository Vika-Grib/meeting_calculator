# Meeting Cost Calculator
Meeting Cost Calculator is a web application that helps you calculate the cost of your meetings based on the average salary and the duration of the meeting. You can either manually enter the duration of the meeting or use the built-in timer.

# Features
Calculate meeting cost based on the number of participants and their average salary.
Option to manually input the duration or use the built-in timer.
View total time and cost spent on meetings from Google Calendar.

![2024-06-10 14 15 16](https://github.com/Vika-Grib/meeting_calculator/assets/130666532/60c1ca8a-683c-4516-ac4a-dc818753d58a)

## Installation

### Clone the repository:
```bash
git clone https://github.com/yourusername/meeting_cost_calculator.git
cd meeting_cost_calculator ```

### Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
```

### Install the required packages:
```bash
pip install -r requirements.txt
```

### Run the application:
```bash
python manage.py runserver
```

Open your web browser and navigate to http://127.0.0.1:8000/ to access the Meeting Cost Calculator.


Usage
Enter the number of participants and their average salary.
Choose whether you know the duration of the meeting or not:
If you know the duration, enter the duration in minutes.
If you don't know the duration, start the timer.
Click "Calculate Cost" to see the cost of your meeting.
Google Calendar Integration
You can also view the total time and cost spent on meetings from your Google Calendar. Log in with your Google account and select the calendar, start date, and end date to see the summary.

Contributing
Feel free to contribute to this project by submitting issues or pull requests. Please follow the standard GitHub guidelines for contributing to open-source projects.

License
This project is licensed under the MIT License. See the LICENSE file for more details.
