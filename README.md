# TickTick-Repeat
Simple Flask Site to add repeating tasks to TickTick.

I'm not a fan of how recurring tasks in TickTick have identical tags (ie you add a tag to one, you add it to all of them). I had made this for batch adding tasks to Notion back when I was using it, and it was simple enough to convert it to TickTick.

It's currently available at [tick.eastonpots.com](https://tick.eastonpots.com/). If you're not comfortable sharing your password, you're free to use it locally/host it yourself!

# Running/ Hosting

## Locally
To run locally simply clone, navigate into repo, and run
```python
pip install -r requirements.txt
python app.py
```
It'll then be available at 0.0.0.0:5000.

## Docker
There's also an included dockerfile and docker compose. To run in docker, just run, after cloning and navigating in,
```bash
docker build . -t ticktick-repeat
docker run -it ticktick-repeat
```
or with docker-compose
```bash
docker-compose up -d
```
It'll then be available at 0.0.0.0:5000.