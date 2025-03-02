Elevator.py - An Elevator Simulator

Assumptions
  - Elevator needs to Move up and down to X amount of floors
  - Elevator has external call buttons and an internal panel with floor select buttons
  - Will attempt to stop at any floor that is in queue and has the same desired direction of travel
  - Will transport passengers to desired floors
  - Doors will automatically open when the desired floor is reached
  - Doors will close regardless if= button on internal panel is selected
  - Will ignore any duplicate floor + travel direction requests
  - Elevator has weight limit that will stop any movement when exceeded

Missing Features:
  - create a GUI to simulate the external buttons and interior panel
  - Add functionality where button select timeout will automatically proceed the program. User has to hit 'Enter' right now
  - add a logging system instead of using stdout
  - Implement unit tests (pyunit) and add more error handling
  - There is still room for refactoring and simplifying some functions
  - set up a time range where the Elevator could be active
  - Set up an asynchronous way for floor requests from outside button to be added to queue while main function runs
  
Potential Enhancements: 
  - Allow for a bank of elevators
  - In a bank of Elevators coordinate the floor requests and send the closest elevator
  - Have a Gui that shows the actual Elevator and passenger movement
  - implement a 'Severance' floor and have it change a passenger’s memories based on which direction it was passed
