# Configure the bot

## Add your token

You must provide the token to your discord bot in the .env file first.

Navigate to the .env.example file. Rename this file to .env.

Provide your token after the `DISCORD_TOKEN=`

As an example

`DISCORD_TOKEN=1234567890`

This is a good guide on how to get your token from the Discord Developer Portal:
https://discordgsm.com/guide/how-to-get-a-discord-bot-token

# Setup Docker Environment

Run ./tools/build_docker.sh to build the docker container.

Run ./tools/run_docker.sh to run the docker container and bot.

> If you want to run this bot in the background of a server, I recommend using screen or tmux.
