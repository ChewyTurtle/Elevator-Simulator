# elevator.py
import time
import sys
from collections import namedtuple, deque
# deque is very similar to Java Double-Ended Queue from what I understand
from pprint import pprint as pp
# I use pprint mostly for troubleshooting and development
from threading import Timer
from random import randint

# GLOBALS - using globals for quick editing and to avoid 'magic numbers'
MAX_FLOOR = 10
MIN_FLOOR = 1
MAX_WEIGHT = 2000 # 2,000 pounds seems pretty typical
ELEVATOR_FPS = 2 # Floors per second (Google says 1-3 is the average for shorter building...)
DOOR_SPEED = 4 # Seconds (best guess based on personal experience)
HEADER_DASHES = 72

# NAMED TUPLE GLOBALS
# I like using named tuples as immutable mini 'classes'

CALL = namedtuple("Call", "down up waiting_passengers") # Would likely make a JAVA class for elevator calls
# 'down' and 'up' variables are boolean and 'waiting_passengers' is a list of passenger named tuples 

PASSENGER = namedtuple("Passenger", "age height weight")# Would likely make a JAVA class for passengers
# age, height, weight are all integers
# Could add other PPI like 'name' or 'gender' but don't think that's in scope for an elevator

# This object was mostly for fun, but could use it as a map for labeling floors, or some other sort of lookup
FLOOR_STRINGS = {
    1: "st Floor",
    2: "nd Floor",
    3: "rd Floor",
    4 : "th Floor: Mens Wear" # old joke I don't remember the origin of - I think it might have been 1st floor
    } 

class Elevator:
    def __init__(self):
        self.current_floor = MIN_FLOOR # Assume elevator is parked on it's lowest floor (may not apply to buildings with basement levels)
        self.direction = 'UP' if self.current_floor <= MAX_FLOOR/2 - 1 else "DOWN" # using roughly the middle floor to determine default directions
        self.request_dir = ""
        self.doors_open = False
        self.passengers = deque()

        # button_lights keeps track of the buttons inside the elevator
        self.button_lights = {i : 'off' for i in range(MIN_FLOOR, MAX_FLOOR + 1)}

        # floors_waiting and waiting_que keep track of outside elevator up and down call buttons
        self.floors_waiting = {i : None for i in range(MIN_FLOOR, MAX_FLOOR + 1)}
        self.waiting_que = deque()

    #### Public Functions ####
    def move_elevator(self):
        """
        Description: Main class of script. Will run if there are already values in self.waiting_que. 
        If waiting_que is empty it will launch the terminal interface that simulates people pressing the external call buttons
        """

        print(f"Elevator at Floor {self.current_floor}\n")
        while len(self.waiting_que) > 0:
            called_floors = set() # Keep track of floors that were selected by either call button, or internal panel

            dest_floor = self.waiting_que.popleft()
            print(f"\nCalled to floor {dest_floor}")
            self._print_panel_lights()

            if self.current_floor != dest_floor:
                called_floors.add(dest_floor)
            
            # Set elevators requested direction
            if self.floors_waiting[dest_floor].up:
                self.request_dir = "UP"
            elif self.floors_waiting[dest_floor].down:
                self.request_dir = "DOWN"

            # Check for requests that are on the way, and are going the same direction
            if self.request_dir == "DOWN":
                for i in range(self.current_floor, MIN_FLOOR -1, -1):
                    # print(i)
                    if self.floors_waiting.get(i) and self.floors_waiting[i].down:
                        called_floors.add(i)
                        if i in self.waiting_que:
                            self.waiting_que.remove(i)

            elif self.request_dir == "UP":
                for i in range(self.current_floor, MAX_FLOOR + 1):
                    if self.floors_waiting.get(i) and self.floors_waiting[i].up:
                        called_floors.add(i)
                        if i in self.waiting_que:
                            self.waiting_que.remove(i)

            # Iterate through all floors towards the destination floor, stopping on floors on the way
            called_floor_que = self._sort_queue(called_floors)

            while len(called_floor_que) > 0:
                print(called_floor_que)
                next_floor = called_floor_que.popleft()
                self.goto_floor(next_floor)

                # Check if any internal elevator buttons have been pushed
                # And add floors to queue if they're on the way.
                additional_stops = self._check_int_button_on_the_way_stops()

                if additional_stops:
                    for stop in additional_stops:
                        if stop not in called_floor_que:
                            called_floor_que.append(stop)
                    # re-sort the queue if new stops were added.
                    called_floor_que = self._sort_queue(called_floor_que)

                # IF no more stops in current direction, change direction and check again
                if len(called_floor_que) == 0:
                    if self.request_dir == "UP":
                        self.request_dir = "DOWN"
                    else:
                        self.request_dir = "UP"
                    additional_stops = self._check_int_button_on_the_way_stops()
                    
                    if additional_stops:
                        for stop in additional_stops:
                            if stop not in called_floor_que:
                                called_floor_que.append(stop)
                        
                        # re-sort if floors were added
                        called_floor_que = self._sort_queue(called_floor_que)
        
        if len(self.waiting_que) == 0:
            self._update_floor_waiting_queue()
            if len(self.waiting_que) > 0:
                self.move_elevator()
            else:
                # If there are no more stops left go back to ground, and have all passengers exit
                self.goto_floor(1)
                self._offload_passengers()

    def goto_floor(self, dest_floor: int):
        above_weight_limit = self._check_if_over_max_load()
        
        if above_weight_limit:
            print(f"Elevator about weight limit. passengers must exit")
            stranded_passengers = self._last_passengers_on_get_off(above_weight_limit)
            print(f"{len(stranded_passengers)} exited elevator on {self.current_floor} and will be added back to the que")
            direction = self.request_dir if self.request_dir else self.direction

            self._que_up_stranded_passengers(stranded_passengers, self.current_floor, direction)
        
        if dest_floor and dest_floor != self.current_floor:
            # Calculate the difference between floors needed to travel to destination floor
            high_floor = max(self.current_floor, dest_floor)
            low_floor = min(self.current_floor, dest_floor)
            diff = high_floor - low_floor

            # Set the elevators direction towards target floor
            if high_floor == self.current_floor or self.current_floor == MAX_FLOOR:
                self.direction = "DOWN"
            elif low_floor == self.current_floor or self.current_floor== MIN_FLOOR:
                self.direction = "UP"

            # Update Elevator Stats
            self.current_floor = dest_floor

            # Sleep to simulate moving to floor
            travel_time = float(diff/ELEVATOR_FPS)
            print(f"\n{'-'*HEADER_DASHES}\n| Next Floor: {dest_floor}\n{'-'*HEADER_DASHES}")
            # Moving an elevator can take a lot of time. No wonder video game developers us them a loading mechanisms
            self._print_loading_dots(travel_time, f"\t- Elevator going {self.direction.title()}")
            floor_string = FLOOR_STRINGS[dest_floor] if dest_floor in FLOOR_STRINGS.keys() else "th Floor"
            print(f"{'-'*HEADER_DASHES}\n|{'*'*5} DING! {dest_floor}{floor_string} {'*'*5}\n{'-'*HEADER_DASHES}")

            self._open_doors()
            self._print_panel_lights()
            self._close_doors()
            # Turn of panel light when on that floor
            self.button_lights[dest_floor] = "off"

    def call_elevator_interface(self):
        start_floor = MIN_FLOOR - 1 # Setting dynamically assuming a building could have basement floors represented by negative numbers
        up_or_down = ''

        while start_floor < MIN_FLOOR or up_or_down == "":
            print("Please enter the floor you're on, and the direction you want to go (up or down) separated by a space")
            args = input("$: ").split(" ")
            if args[0].isdigit() and args[1].lower() == 'down' or args[1].lower() == 'up':
                # try:
                start_floor = int(args[0])
                if MIN_FLOOR <= start_floor <= MAX_FLOOR:
                    up_or_down = args[1].upper()
                    
                    down_bool = True if up_or_down =="DOWN" else False
                    up_bool = True if up_or_down == "UP" else False

                    if start_floor == MIN_FLOOR:
                        self.floors_waiting[start_floor] = CALL(down = False, up = True, waiting_passengers = [])
                        self.waiting_que.append(start_floor)
                    elif start_floor == MAX_FLOOR:
                        self.floors_waiting[start_floor] = CALL(down = True, up = False, waiting_passengers = [])
                        self.waiting_que.append(start_floor)
                    else:
                        self.floors_waiting[start_floor] = CALL(down_bool, up_bool, [])
                        self.waiting_que.append(start_floor)

                else:
                    print(f"Start Floor must be between {MIN_FLOOR} - {MAX_FLOOR}")
                    start_floor = MIN_FLOOR - 1
                    up_or_down = ""
                # except:
                    print(f"Invalid Floor Number: Please enter a number between 1 - 10 for your current floor and 'up' or 'down' for your direction")
            else:
                print(f"Invalid Floor Number: Please enter a number between 1 - 10 for your current floor, and up' or 'down' for your direction")

    ##### Private non void functions ####

    def _last_passengers_on_get_off(self, above_weight: bool) -> list:
        stranded_passengers = []

        while above_weight:
            # Last passenger added gets off
            removed_passenger = self.passengers.pop()
            # Passengers will queue again on floor they had to exit on
            stranded_passengers.append(removed_passenger)
            above_weight = self._check_if_over_max_load()
        
        return stranded_passengers

    def _check_if_over_max_load(self) -> bool:
        above_weight = False
        total_weight = 0
        if len(self.passengers) > 0:
            total_weight = sum([p.weight for p in self.passengers])
        print(f"\t - Elevator Load = {total_weight} pounds")
        if total_weight >= MAX_WEIGHT:
            above_weight = True
        return above_weight

    def _check_int_button_on_the_way_stops(self) -> set:
        print(f"\t - Checking for active panel buttons for floors on the way {self.request_dir}")

        additional_destinations = set()
        if  self.request_dir == "DOWN":
            for i in range(self.current_floor, MIN_FLOOR -1, -1):
                if self.button_lights.get(i) == 'on':
                    additional_destinations.add(i)
        if self.request_dir == "UP":
            for i in range(self.current_floor, MAX_FLOOR + 1):
                if self.button_lights.get(i) == 'on':
                    additional_destinations.add(i)

        return additional_destinations

    def _sort_queue(self, que) -> deque:
        if self.request_dir == 'DOWN':
            que = sorted(que, reverse=True)
        else:
            que = sorted(que)

        return deque(que)


    #### Private void functions ####

    def _que_up_stranded_passengers(self, stranded_passengers: list, floor: int, direction: str):
        up_bool = False
        down_bool = False

        if direction == "UP":
            up_bool = True
        elif direction == "DOWN":
            down_bool = True

        self.floors_waiting[floor] = CALL(down_bool, up_bool, stranded_passengers)
        self.waiting_que.append(floor)

    def _create_passenger(self):
        # Admittedly this is more of a function that could be used for testing

        age = randint(0, 99) # I think it's funny some lego sets are for ages X - 99
        height = 0 # inches
        weight = 0 # lbs

        # Could use a case statement if written in JAVA
        if age in range(0, 1):
            weight = randint(0, 15)
            height = randint(12, 24) # closish to how tall babies are?
        elif age in range(1, 7):
            weight = randint(15, 50)
            height = randint(20, 50) # closish to toddler - young child height?
        elif age in range(7, 15):
            weight = randint(50, 120)
            height = randint(40, 60)
        else:
            weight = randint(100, 350)
            height = randint(40, 90) # Not sure how many people are above 7ft - 6inches, but i'll assume a few
        
        rand_passenger = PASSENGER(age, height, weight)
        return rand_passenger

    def _add_passengers(self):
        passengers_boarded = 0

        if self.floors_waiting[self.current_floor] and self.floors_waiting[self.current_floor].waiting_passengers:
            for p in self.floors_waiting[self.current_floor].waiting_passengers:
                self.passengers.append(p)
                passengers_boarded += 1
        else:
            num_of_passengers = randint(1,5) # Assuming small group of people on each floor
            for _ in range(num_of_passengers):
                self.passengers.append(self._create_passenger())
                passengers_boarded += 1
        
        print(f"\t - {passengers_boarded} Passengers boarded the elevator")

    def _offload_passengers(self):
        passengers_exited = 0
        passengers_leaving = []
        floors_waiting = True if len(self.floors_waiting) > 0 else False
        # Maybe list comprehension inside of a len > 0 evaluation is too 'Pythonic'?
        active_buttons = True if len([b for b in self.button_lights if self.button_lights[b] == 'on']) > 0 else False

        # There are floors still in the travel queue
        if (active_buttons or floors_waiting):
            for passenger in self.passengers:
                if randint(1, 4) == 3: # 1/3 chance to get off on a floor
                    passengers_leaving.append(passenger)
                    passengers_exited += 1

            if passengers_leaving:
                for passenger in passengers_leaving:
                    self.passengers.remove(passenger)
                        
        elif not floors_waiting and not active_buttons: # If there are no more stops, everyone gets off
            if self.passengers:
                for _ in range(len(self.passengers)):
                    self.passengers.popleft()
                    passengers_exited += 1
        
        print(f"\t - {passengers_exited} Passengers exited on floor")

    def _open_doors(self):
        self._print_loading_dots(DOOR_SPEED, "\t- Doors opening")
        self.doors_open = True
        # Proper elevator etiquette suggests it's best to let people off the elevator first\
        if self.passengers:
            self._offload_passengers()

        self._check_internal_destinations(DOOR_SPEED*3)

    def _close_doors(self):
        # Before closing the doors, allow for passengers to get on
        # I think there are supposed to be sensors on the doors so they don't close while you're boarding
        # Either some elevators aren't that sophisticated, or I've encountered a lot of broken ones before.
        self._add_passengers()
        self._print_loading_dots(DOOR_SPEED, "\t - Closing Doors")
        self.doors_open = False

    def _update_floor_waiting_queue(self):
        """Description - Intended to run when the variable called_floor_que is empty.  Function will simulate adding new call requests
        or will allow for input to exit the elevator program"""
        new_calls = 0
        if len(self.waiting_que) == 0:
            while new_calls == 0:
                try:
                    # max calls should be 2 less than the MAX_FLOOR * 2.  Each floor can have an up or down button, except the top and bottom floors
                    max_calls = (MAX_FLOOR * 2) - 2
                    new_calls = int(input(f"No waiting calls in queue. Enter desired number of new calls ({MIN_FLOOR} - {max_calls}) 0 to exit: "))
                    
                except:
                    print(f"input must be a digit between {MIN_FLOOR} - {max_calls} or 0 to exit")
                
                if MIN_FLOOR <= new_calls <= (MAX_FLOOR*2) - 2: 
                    # Maximum amount of new calls assumes each floor could have both up and down on except top and bottom floor which only have up or down
                    for i in range(1, new_calls + 1):
                        self.call_elevator_interface()

                elif new_calls == 0:
                    # Setting to higher than MAX_FLOOR to exit input loop
                    new_calls = MAX_FLOOR + 1
                else:
                    print(f"input must be a digit between {MIN_FLOOR} - {MAX_FLOOR * 2} or 0 to exit")

    def _check_internal_destinations(self, timeout: int):
        buttons_pressed = []
        # This Python threading Timer function still requires user to hit enter to get past prompt
        # There is no cross platform solution to automatically hitting 'Enter'
        # There are non standard Library modules that could be used to do this better, but I wanted to stick to 'Vanilla' Python

        # TODO - to keep standard Library compatibility build function to identify OS and automatically hit 'Enter' for whatever OS 
        # elevator.py is running in
        t = Timer(timeout, lambda: print(f"No button pressed...\nPress Enter to Close Doors"))
        t.start()
        try:
            buttons_pressed = input(f"\nEnter your destination floor(s) ({MIN_FLOOR} - {MAX_FLOOR}) multiple floors separated by space: ")
            if " " in buttons_pressed:
                buttons_pressed = buttons_pressed.split(" ")
            else:
                buttons_pressed = [buttons_pressed]
        except:
            buttons_pressed = []

        for button in buttons_pressed:
            try:
                button = int(button)
            except:
                button = 0
            if button >= MIN_FLOOR and button <= MAX_FLOOR:

                if button in self.button_lights.keys():
                    self.button_lights[button] = "on"

        t.cancel()
    
    def _print_loading_dots(self, duration: int, travel_string: str, interval=0.25):
        sys.stdout.write(travel_string)
        start_time = time.time()
        while abs(time.time() - start_time) < duration:
            sys.stdout.write(".")
            sys.stdout.flush()
            time.sleep(interval)
        print()          

    def _print_panel_lights(self):
        status_char = '-'
        line_display = []
        lights_on = 0
        for floor, status in self.button_lights.items():
            if status == 'on':
                status_char = '*'
                lights_on += 1
            else:
                status_char = '-'
            line_display.append(f"{floor}: {status_char}")
        
        print("-"*HEADER_DASHES)
        print("| " + " | ".join(line_display) + " |")
        print("-"*HEADER_DASHES)

        # I love this scene in Elf when he pushes all the buttons in the Empire State Building Elevator
        if lights_on == MAX_FLOOR:
            christmas_string = f"{'*'*5} IT LOOKS LIKE A CHRISTMAS TREE! {'*'*5}"
            print(f"|{christmas_string.center(HEADER_DASHES - 2)}|")
            print("-"*HEADER_DASHES)
        

if __name__ == '__main__':
    elevator = Elevator()
    print("Welcome to the Elevator.\nA Business with ups and downs")
    elevator.move_elevator()
