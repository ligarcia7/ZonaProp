This program is designed to extract real estate ads from a few websites and send them to a Telegram chat using a Telegram bot. To run the program, you'll need to install some Python packages. The required packages and their versions are listed in the `requirements.txt` file.

To install the packages, you can use the following command in your terminal or command prompt:

`pip install -r requirements.txt`

This command will read the `requirements.txt` file and install the packages and their dependencies.

It's recommended that you create a new virtual environment before installing the packages, to avoid conflicts with other Python projects or packages installed on your system. You can use a tool like `virtualenv` or `conda` to create a new environment.

Once you've installed the required packages, you'll need to create a Telegram bot and a chat room to receive the ads. Instructions on how to create a bot and a chat room can be found in the Telegram documentation [here](https://core.telegram.org/bots#3-how-do-i-create-a-bot).

After you've created the bot and the chat room, you'll need to obtain the bot ID and the chat room ID and save them in a JSON file called `telegram_bot_keys.json`. The JSON file should have the following format:


{
"botID": "your_bot_id_here",
"roomID": "your_room_id_here"
}

Replace `your_bot_id_here` and `your_room_id_here` with the actual bot ID and room ID you obtained from Telegram.

Once you've set up the bot and the chat room, you can run the program by running the `main.py` file. The program will extract ads from the specified websites and send them to the Telegram chat. The program will keep running until you stop it manually, so you can run it in the background or schedule it to run at specific times using a tool like `cron` (on Linux) or the Task Scheduler (on Windows).

If you encounter any issues or have any questions, feel free to contact the developer.