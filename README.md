<a name="readme-top"></a>

<!-- PROJECT LOGO/HEADER -->
  <h3 align="center">Degrees of Freedom Strategy & Scouting tools and systems</h3>

  <p align="center">
    The scouting system and tools used by FRC Team 6413, Degrees of Freedom, for the 2026 season - Rebuilt.
  </p>
</div>

## Introduction

The DoF scouting & strategy system consists of a web page, Python scripts and a MongoDB database (or two).  The web page is used by scouts to collect match data at events.  Data is stored in a QR code that gets displayed on the tablet and scanned via a Bluetooth barcode scanner which is paired to a laptop running a Python script which "reinflates" the data and saves it to a local and/or remote MongoDB database.  The data in the MongoDB is visualized using the strategy dashboard written in Python using Streamlit.  It can also be used by other entities such as a Slackbot (eventually).

## Environment setup

This repo uses **uv** to manage Python and all required packages. uv handles everything automatically — no manual virtual environment creation or `pip install` commands needed.

**For full setup instructions and a complete list of commands for running every script in this repo, see [UV_SCRIPTS.md](UV_SCRIPTS.md).**

### Quick start

**Step 1: Install uv** (one-time per computer)

Here are 3 different ways to install uv on your computer.  The first step is to open an Admin Powershell or Command Prompt on Windows or a Terminal if on a Mac.  We will refer to whatever you opened as "the Terminal" from this point on to keep things readable.

- If you already have Python installed then you can use it to install uv by typing:
  - On Windows: **pip install uv**
  - On Mac: **pip3 install uv**
- If Python is not installed, you have other ways to install the standalone uv:
    - If chocolatey is installed: **choco install uv**
    - If chocolatey is not installed, type the following:
      - On Windows: **powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"**
        - This will also add uv to your system PATH so it will always be available going forward.
      - On Mac you have 2 options:
        -- Use Homebrew: **brew install uv**
        -- Power user style: **curl -LsSf https://astral.sh/uv/install.sh | sh**

Once you have installed uv, test it by running **uv --version**.  If you do not see any version information, you need to recheck your installation.

**Step 2: Sync dependencies** (one-time per repo clone, run from the repo root)

- On Windows type **uv sync --link-mode=copy**
- On Mac/Linux type **uv sync**

That’s it — uv will download the correct Python version and all required packages automatically.

**Note:** The BAT files in the root of the repo handle everything above for you on Windows. Simply double-click the relevant BAT file in File Explorer and it will run the correct script with all dependencies available.  Feel free to make a shortcut to them on your Desktop to easily start the scripts up.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

**Step 3: Docker Desktop & MongoDB**

###Windows

To run Docker Desktop on Windows your computer must must meet specific requirements, particularly regarding virtualization and the Windows Subsystem for Linux (WSL).

1. Check System Requirements
  - OS: Windows 10/11 64-bit (Home, Pro, Enterprise, or Education) version 21H2 or higher.
  - Hardware: At least 4GB of RAM and a 64-bit processor.
  - Virtualization: **MUST* be enabled in your computer’s BIOS/UEFI settings. You can verify this in Task Manager > Performance tab > CPU.  Look for "Virtualization: Enabled" 

2. Enable Required Windows Features 
  - Docker typically uses the WSL 2 backend for better performance so make sure you have it installed:
    - Open the Start menu, search for **Turn Windows features on or off**, and open it.
    - Ensure Windows Subsystem for Linux and Virtual Machine Platform are checked.
    - Click **OK** and restart your computer if prompted.
  - Alternatively, you can run **wsl --install** in an Admin PowerShell to set this up automatically.

3. Download and Install Docker Desktop 
  - Visit the [Docker Website](https://www.docker.com/products/docker-desktop/) and click **Download for Windows**.
  - Run the downloaded installer.
    - When prompted, ensure the **Use WSL 2 instead of Hyper-V** option is selected.
  - Follow the remaining wizard instructions and click **Close** and restart once finished to complete the installation.

4. Initial Setup and Verification
  - Open Docker Desktop from the Start menu or desktop shortcut.
  - Review and accept the Docker Subscription Service Agreement.
  - You can sign in with a Docker ID or skip this step to go straight to the dashboard.  There is no benefit to signing in so we recommend skipping it.
  - Open a terminal and type **docker --version**.  If the installation was successful you will get the current Docker version number and Docker is ready to go.
  - In the terminal type the following to ensure the engine is working: **docker run hello-world**
    - This will download a small test image and run it in a container.  You should see a nice Hello message confirming Docker is installed and working properly.  If not, recheck your steps or check the Docker documentation on how to troubleshoot.

5. Install the MongoDB image:
  - In the terminal type: **docker pull mongo:8.0**.  This will install the 8.x version of the MongoDB server to use locally.  For this year we are going to pin to 8.x since we had been pinned to 6.x but that is now EOL.

**NOTE:** When you launch your first MongoDB container, make sure you configure the container to have an exposed port of 27017 or else you will not be albe to contact the server.


###Mac

Here are the steps to install Docker Desktop on Mac:

1. Download the appropriate DMG installer (Apple silicon or Intel chip) from the [Docker website](https://docs.docker.com/desktop/setup/install/mac-install/).
2. Open the file you downloaded and drag the Docker icon to the Applications folder.
3. Open Docker from your Applications folder, accept the subscription agreement, and grant necessary permissions.
  - Alternatively you can use HomeBrew to install it: **brew install --cask docker-desktop**
4. Verification:
  - Open the Terminal and run **docker --version**.  If the installation was successful you will get the current Docker version number and Docker is ready to go.
  - In the terminal type the following to ensure the engine is working: **docker run hello-world**
    - This will download a small test image and run it in a container.  You should see a nice Hello message confirming Docker is installed and working properly.  If not, reche
5. Install the MongoDB image:
  - In the terminal type: **docker pull mongo:8.0**.  This will install the 8.x version of the MongoDB server to use locally.  For this year we are going to pin to 8.x since we had been pinned to 6.x but that is now EOL.

**NOTE:** When you launch your first MongoDB container, make sure you configure the container to have an exposed port of 27017 or else you will not be albe to contact the server.

**NOTES:**
Apple Silicon (M1/M2/M3): Use the Apple Silicon version for native performance.
Rosetta 2: If asked, install Rosetta 2 for running x86_64 binaries.


## Credentials setup

API keys and database connection strings are kept in a `credentials.py` file in each package directory. This file is gitignored and NEVER committed — each person sets up their own copy.

For each directory where you'll run scripts, copy the example file and fill in your values:

```
Scouting-Scripts/credentials.py.example  →  Scouting-Scripts/credentials.py
Strategy-Dashboard/credentials.py.example  →  Strategy-Dashboard/credentials.py
```

The three values in each file are:

- **TBA_AUTH_KEY** — your The Blue Alliance API key (get one at thebluealliance.com/account)
- **PRIMARY_CONNECTION_STRING** — your MongoDB connection string (required)
- **SECONDARY_CONNECTION_STRING** — a second MongoDB to mirror data into (optional, leave as `""` if unused)

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Next steps

The repo has multiple folders to organize our various scripts based on how they are used:

- Scouting-App: The web page "app" we used for match scouting during events.
- Scouting-Scripts: The scripts used to collect the data from the app and store it into our MongoDB database(s).  There are also scripts here for doing pre-scouting work for an event.
- Strategy-Dashboard: Our Streamlit based dashboard for visualizing and sifting the data we colleted during an event.
- Tools: A collection of utility scripts such as random data generation.

So where you go from here depends on what you are trying to do with Scouting and Strategy.  Below are more detailed descriptions on how to use each of the folders correctly. 

### Scouting App

The scouting app web page uses the TBA event code stored in the config.js file to decide what event data to load.  Simply change the **eventCode** value in that file to pick a different event.  The scouting app is designed for the 2025 game.  We will be making a new repo for each year to keep things clean and separate.  Check out our GitHub page and finding the repo for the year you want.

Scouting is done by simply loading the contents of the **Scouting-App** folder and then opening the index.html file in a browser.  The page will load the Javascript files it needs to configure itself and to get functionality to read from The Blue Alliance and generate QR codes.

There are 3 easy ways to use the page:

1. To run the app locally simply grab a copy of the entire **Scouting-App** folder in this repo and simply double click on the index.html file.
2. Run a local web server like the <a href="https://www.rebex.net/tiny-web-server/">Rebex Tiny Web Server</a> to host the file on your local network.  Copy the entire **Scouting-App** folder in this repo to the web servers data directory.
3. Put all of the contents of the **Scouting-App** folder on an Internet accessible web server and then load it with any browser.

For events we typically go with option 3.  However there are times when the other 2 options are used so pick what suites your needs.

Once the page is loaded, fill out the various fields.  When you are done scouting a match, click on the **Get QR Code** button at the bottom.  All of the data on the page will be encoded as a JSON object in the QR code on the page.  You can either scan the QR code between matches or you can save them for later and scan them at a more convenient time.

To collect the data via the QR code from the app you will also need to run the scripts in the **Scouting-Scripts** folder.  Read the next section for more details on that.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Data collection

The data collected from the Scouting App is collected using QR codes, a barcode scanner paired to a computer and a Python script that will 'reinflate' the JSON data in the QR code into a more dataviz friendly format that gets stored into a MongoDB locally and/or remotely.

**Note:** In the middle of the 2025 season we created BATch scripts to automate the data collection process.  Simply run the **Scouting Match v8 Scan.bat** script by double clicking on it in File Explorer or manually typing the name in any command prompt opened to this repo.

To run the data collection script, use uv from the repo root (see [UV_SCRIPTS.md](UV_SCRIPTS.md) for the full command reference):

**uv run --package frc-6413-scouting-scripts python Scouting-Scripts/scouting_2025.py**

From there, simply enter the TBA event code for the event you are collecting data for and then start scanning QR codes to collect data.

When you are done collecting data for the event or for the day simply type in **quit** and the script will exit.  For multiday events you can simply repeat the steps above on the subsequent days and the data you collect will get added to what was already collected.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Strategy Dashboard

The Strategy Team created a dashboard using Streamlit to visualize the scouting data that gets saved into the MongoDB. The dashboard is intended to help with several tasks like:

- Adjusting match stratgies for upcoming matches
- Getting an idea of each robots strengths, weaknesses as well as their tactics
- Making our picklist choices

### Dashboard usage

**Note:** In the middle of the 2025 season we created BATch scripts to automate starting the Dashboard.  Simply run the **Strategy Dashboard.bat** script by double clicking on it in File Explorer or manually typing the name in any command prompt opened to this repo.

To see the dashboard, use uv from the repo root (see [UV_SCRIPTS.md](UV_SCRIPTS.md) for the full command reference):

**uv run --package frc-6413-strategy-dashboard streamlit run Strategy-Dashboard/main.py**

That will start the dashboard and provide you with the URL to access it locally (or to share with others on the same network).

Any interactions with the dashboard should rerun the app. With constant interactions, most data points will update around every 90 seconds if new data is being collected while the dashboard is in use. If an urgent data update is necessary: the sidebar "Refresh Scouting Data" or "Refresh Match Schedule" buttons will force a refresh of the respective data types.

#### Event code selection

When you first open the page, you should select the current event code and the data event codes.

- **Current Event Code** is the event code you are currently at or looking for data in anticipation of. It's the event code that is used to get all the team numbers, match schedule, etc.
- **Data Event Codes** is a list of event codes containing every event you want the dashboard to use data from. If you want to only look at data from the current competition, remove everything except that entry.

#### Brief overview of pages

- **All Teams**: A page comparing all teams attending the selected current event with box plots and a table.
- **Team Summary**: A simple page for summarizing scouting and prescouting information on a team. You can also add multiple teams to the input to compare them.
- **Match Schedule**: The full match schedule table (received from fetching The Blue Alliance). 
- **Match Scouter**: A page where you can scout a future match to formulate match strategy. It will compare and sumamrize the alliances in the match.
- **Alliance Explorer**: A page where you can create speculative or real alliance scenarios. It will compare and summarize the speculative alliances.
- **Niche Finder**: A page for finding teams that fulfill specific niches. The core idea is that comparing teams on a stat based solely on their average is an ineffective method of finding the "best" teams at something in a game based on specializations that can shift from match-to-match. Instead, this lets you to view upper quartiles and maxs to find the teams that have the highest ceiling. It can also adjust for accuracy to discredit the high ceiling yet inaccurate teams.

#### Properly closing the dashboard

**NOTE:** When you are done using the dashboard you should shut it all down in the following order:

- Press **Ctrl-C** in the terminal where you started the dashboard.  This will stop the process cleanly.
- Close the dashboard's browser tab.  If you do this before the step above, you will not be able to use Ctrl-C to stop the process; you will need to use the Task Manager to find and kill the process.


<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Prescouting

We collect our pre-scouting data in a Google Doc in our sponsors Google Workspace.  The format of the prescouting is not arbitrary since we need to extract the pre-scouting data and export it to our MongoDB for use by our other tools and Slackbot.  To make the process of pre-scouting easier we use two Python scripts in the **Scouting-Scripts** directory: **prescouting_make_template.py** and **prescouting_upload.py**.  The former script creates a Markdown formatted template that we then bring into Google Docs to fill out.  The latter script is used to take the pre-scouting data from a Markdown formatted file and import it into our MongoDB.

### Step 1: Create a per-event template

For each event you are prescouting for you will create a custom prescouting template.  Run the following from the repo root (see [UV_SCRIPTS.md](UV_SCRIPTS.md) for the full command reference):

- **uv run --package frc-6413-scouting-scripts python Scouting-Scripts/prescouting_make_template.py**
- Enter the TBA event code for the event you are prescouting **FOR**.

After entering a valid event code the script will generate a template using Markdown with all team numbers and names attending the chosen event. 

### Step 2: Import the per-event template into Google Docs

You next need to import the template generated in the previous step into a shared Google Doc.  To import the template file follow these steps:

- Open the template file in any text editor
- Copy the entire contents of the file to the clipboard
- Open your shared Google Doc you plan to use
- Select the "Paste from Markdown" option to paste in the Markdown.

**NOTE: For the Paste from Markdown option to show up, Markdown MUST be enabled in Google Docs under Tools -> Preferences.**

### Step 3: Pre-scout all teams

Use your preferred resources to collect pre-scouting data about each team in the Google Doc.  In our case we collect their strengths, weaknesses and any interesting observations and tactics.  Put that data in the proper place in the Google Doc.

### Step 4: Export the data from Google Docs

Follow these steps to export the pre-scouting data from Google Docs whenever you want:

- Open the Google Doc
- Export the entire contents as a markdown by selecting **File** -> **Download** -> **Markdown**.

Be sure you save the exported data into the **2026-Strategy-Scouting** directory (aka your local copy of the this repo). If you save it to another directory, simply move it into the **2026-Strategy-Scouting** directory before moving to the next step.

### Step 5: Import the data into MongoDB

At any time you can import (or re-import) the pre-scouting data into your MongoDB.  If you re-import the data, any data you imported previosly will be **removed** so make sure you are re-importing your full pre-scouting data and not a subset of it.

Run the following from the repo root, giving it the name of the file you want to import (see [UV_SCRIPTS.md](UV_SCRIPTS.md) for the full command reference):

- **uv run --package frc-6413-scouting-scripts python Scouting-Scripts/prescouting_upload.py**

Once done the pre-scouting data will have been put into the MongoDB that is configured in your **credentails.py** file.  

You can now use whatever tools you want to access that data from the config.V5_COL_SCOUTING collection.  All pre-scouting data will have a docType item value of config.DT_SCOUTING_PRESCOUT.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Utilities

We have a collection of helpful utlity scripts in the **Tools** subdirectory in the repo.  The majority are used for generating random scouting data for a full event.

There may be multiple versions of some scripts.  When this occurs, you should typically only run the "most recent" one; the one with the highest version number or modification letter.  For instance if there are scripts named RandomData2025A.py, RandomData2025B.py and RandomData2025C.py then you should run RandomData2025C.py.  The output of these utility scripts will work with the latest script in the **Scouting-Scripts** subdirectory.

**NOTE:** Some scripts in this folder need the config.py and credentials.py found in the **Scouting-Scripts** subdirectory.  To use them simply copy those files into the **Tools** folder before running the script.

All Tools scripts are run from the repo root using uv — see [UV_SCRIPTS.md](UV_SCRIPTS.md) for the full command reference. The general form is:

**uv run --package frc-6413-scouting-tools python Tools/&lt;script_name&gt;.py**

**TODO: Add a detailed description on how to modify the a_Teams array in the RandomData... script for more control over how the data changes.** 

<p align="right">(<a href="#readme-top">back to top</a>)</p>


<!-- CONTACT -->
## Contact

Degrees of Freedom - [@dof6413](https://twitter.com/dof6413) - [Instagram](https://www.instagram.com/dof6413) - [Facebook](https://www.facebook.com/dof6413) - [YouTube](https://www.youtube.com/channel/UCoJrt-wiXr132q2F-QRBeTw) - dof6413@gmail.com

Project Link: [https://github.com/DoF-6413/2026-Strategy-Scouting](https://github.com/DoF-6413/2026-Strategy-Scouting)

<p align="right">(<a href="#readme-top">back to top</a>)</p>


<!-- ACKNOWLEDGMENTS -->
## Acknowledgments

A very big Thank You to the following:

* [The Firewheel Stem Institute (formerly Si Se Puede Foundation) for sponsoring us](https://firewheel.org/)
* [FRC Team 2486 - The CocoNuts for getting us started](https://github.com/coconuts2486-frc)
* [FRC Team 2451 - PWNAGERobotics for portions of their ScoutingPASS system](https://github.com/PWNAGERobotics/ScoutingPASS)

<p align="right">(<a href="#readme-top">back to top</a>)</p>
