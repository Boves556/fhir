# More secured chat system between users
## Usage
This script allows your users to exchange valid(!) FHIR Data as JSON. Serve the data correctly to all authenticated and authorized users.

## How to run the script
Its very easy:
to run the server script:
```
python server.py 3490
```
You can also change the port to anyone of your choice.

to run the client script:
```
python client.py <clientname> password localhost 3490
```
example:
```
python client.py Dr.Waldmann krankenhaus localhost 3490
```
Its important to **note** that you should open muiltiple clients with different client names to be able to text between each other.

# Things to note:
You can also add other usernames and passwords or change the usernames and passwords in the USER_DATABASE section of the server.py script.
```
USER_DATABASE = {
    "Dr.Waldmann": "krankenhaus",
    "Herr.Krankwurst": "immerso",
}
```

This is also a sequel to this code: https://github.com/Boves556/chatui.git 

Please let me know if you encounter any issues or bugs or if you have better ideas on how I can improve the code.
