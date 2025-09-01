.PHONY: lint format format-check

lint:
	flake8 src download_drive_video.py

format:
	autopep8 -r -i src download_drive_video.py

format-check:
	autopep8 -r --diff src download_drive_video.py

