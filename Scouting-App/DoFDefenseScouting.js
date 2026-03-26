// DoFscouting.js (derived from ScoutingPASS.js)
//
// The "guts" of the Scounting application
// Original credit to Team 2451 - PWNAGE
//
// This version has been modified to suit Team 6413's needs with all the extra stuff removed
//
// Key to the field names that need to be in the DOM for the scripts to work properly:
// input_e = TBA Event code
// input_l_## = Match Level to scout (qm, sf, f)
// input_m = Match number (Match-input on our original form)
// input_r_## = Robot position (r1, r2, r3, b1, b2, b3)
// input_t = = Team number (TeamNumber-input on our original form)
//
// Local storage data format:
// Each event has a local storage item named by the event code
// Within each event code is a list of entries that store QR codes
// The contents of each entry are:
// "data" - the stringified JSON used to write the QR code
// "header" - The text used to write the modal header
// "scanned" - A boolean that stores whether or not the QR has been scanned already

/**
* Load the configuration data from the config_data value (found in the YYYY_config.js file that should get loaded separately).
*
* @return -1 if there was an error in the config data, 0 if the configuration was loaded successfully
*/
function configure() {
	try {
		var mydata = JSON.parse( config_data );
		}
	catch ( err ) {
		// Log the error to the console first...
		console.log( `Error parsing configuration file` )
		console.log( err.message )
		console.log( 'Use a tool like http://jsonlint.com/ to help you debug your config file' )
		
		// Then inject it into the top of the web page so scouts can see something is broken!
		var warning = document.getElementById( "header_warning" )
		warning.innerHTML = `Error parsing configuration file: ${err.message}<br><br>Use a tool like <a href="http://jsonlint.com/">http://jsonlint.com/</a> to help you debug your config file`
		return -1
		}

	// Set the page title if we were given one
	// TODO: Leaving this in for now just to test loading from a config file.  Take it out eventually.
	if ( mydata.hasOwnProperty( 'title' ) ) {
		document.title = mydata.title;
		}

	// Set the event code if we were given one
	if ( mydata.hasOwnProperty( 'eventCode' ) ) {
		document.getElementById( "input_e" ).value = mydata.eventCode;
		document.getElementById( "input_ed" ).value = mydata.eventCode + "def"; // ONLY needed for defense scouting
		}

	return 0
	}


/**
* Clear out all of the defense scouting related fields on the form
*/
function clearDefenseScoutingFields() {
	// Clear the red alliance inputs
	clearRadioList( "R1-input" );
	clearRadioList( "R2-input" );
	clearRadioList( "R3-input" );

	// Clear the blue alliance inputs
	clearRadioList( "B1-input" );
	clearRadioList( "B2-input" );
	clearRadioList( "B3-input" );

	// Set all radio buttons to the default ("Not Attempted")
	document.getElementById( "R1-0" ).checked = true;
	document.getElementById( "R2-0" ).checked = true;
	document.getElementById( "R3-0" ).checked = true;

	document.getElementById( "B1-0" ).checked = true;
	document.getElementById( "B2-0" ).checked = true;
	document.getElementById( "B3-0" ).checked = true;

	// Remove the QR code
	$('#qrcode').html( '' );
}

/**
* Clear the data on the form with only minor exceptions to make moving to the next match faster
*/
function resetFormForNextMatch() {
	var match = 0;

	// NO need to save off values we want to keep as we are going to just zap items we want and
	// ignore the rest leaving them alone...

	// Get the match number
	match = parseInt( document.getElementById( "input_m" ).value );

	// Clear the "validated" state of the <BODY>.  This will NOT discard any values.  We have to manually
	// do that ourselves.
	$('body').removeClass( 'was-validated' );

	// Update the match and team numbers for the next match
	if ( match == NaN ) {
		// If we got no match value, zap the match number
		document.getElementById( "input_m" ).value = ""
	    }
	else {
		// Bump the match number then update the team number (and happy text)
		document.getElementById( "input_m" ).value = match + 1
		}

	// Zap the scout initials and then clear out the scouting fields

	document.getElementById( "input_s" ).value = "";

	clearDefenseScoutingFields();

    getAlliances( getCurrentMatchKey() );
}


/**
* Get the robot code for the selected robot on the form.
*
* @return "" if no robot is selected or a value in the format of "z#" where z is either r or b and # is a value between 1 and 3
*/
function getRobot() {
	if ( document.getElementById( "input_r_r1" ).checked ) {
		return "r1";
		}
	else if ( document.getElementById( "input_r_r2" ).checked ) {
		return "r2";
		}
	else if ( document.getElementById( "input_r_r3" ).checked ) {
		return "r3";
		}
	else if ( document.getElementById( "input_r_b1" ).checked ) {
		return "b1";
		}
	else if ( document.getElementById( "input_r_b2" ).checked ) {
		return "b2";
		}
	else if ( document.getElementById( "input_r_b3" ).checked ) {
		return "b3";
		}
	else {
		return "";
		}
	}


/**
* Get the code for the selected match level being scouted on the form
*
* @return "qm" for qualifiers, "sf" for playoffs/double elimination, "f" for finals
*/
function getLevel() {
	if ( document.getElementById( "input_l_qm" ).checked ) {
		return "qm";
		}
	else if ( document.getElementById( "input_l_sf" ).checked ) {	// Was "de" in the original script but that is 110% wrong since TBA does NOT use "de"!
		return "sf";
		}
	else if ( document.getElementById( "input_l_f" ).checked ) {
		return "f";
		}
	else {
		return "";
		}
	}



/**
* Get the team name for the give team number
*
* @param {teamNumber} The team number to get the name for
*
* @return A string that represents the teams name or "" if the team info is not available (or there is no such team number at the event)
*/
function getTeamName( teamNumber ) {
	if ( teamNumber !== undefined ) {
		if ( teams ) {
			var teamKey = "frc" + teamNumber;
			var ret = "";
			Array.from( teams ).forEach( team => ret = team.key == teamKey ? team.nickname : ret );
			return ret;
			}
        else {
		    console.log( "No team data available!" );
		    return "";
		    }
		}

    console.error( "No team number provided!" )
 	return "";
	}


/**
 * Populates the team number DOM elements based on the alliance data for a given match key.
 *
 * @param {string} matchKey The TBA match code for the currently selected match and event.
 */
function getAlliances(matchKey) {
    if (matchKey !== undefined && schedule) {
        const match = Array.from(schedule).find(match => match.key === matchKey);

        if (match && match.alliances) {
            const redTeams = match.alliances.red.team_keys;
            const blueTeams = match.alliances.blue.team_keys;

            // Populate red alliance team numbers
            document.getElementById("r1teamnum").textContent = redTeams[0].replace("frc", "");
            document.getElementById("r2teamnum").textContent = redTeams[1].replace("frc", "");
            document.getElementById("r3teamnum").textContent = redTeams[2].replace("frc", "");

            // Populate blue alliance team numbers
            document.getElementById("b1teamnum").textContent = blueTeams[0].replace("frc", "");
            document.getElementById("b2teamnum").textContent = blueTeams[1].replace("frc", "");
            document.getElementById("b3teamnum").textContent = blueTeams[2].replace("frc", "");
            }
        else {
            // Clear team number elements if match is not found or alliances are missing
            document.getElementById("r1teamnum").textContent = "";
            document.getElementById("r2teamnum").textContent = "";
            document.getElementById("r3teamnum").textContent = "";
            document.getElementById("b1teamnum").textContent = "";
            document.getElementById("b2teamnum").textContent = "";
            document.getElementById("b3teamnum").textContent = "";

            console.error(`Match with key ${matchKey} not found or alliance data is missing.`);
            }
        }
    else {
        // Clear team number elements if matchKey is undefined or schedule is missing
        document.getElementById("r1teamnum").textContent = "";
        document.getElementById("r2teamnum").textContent = "";
        document.getElementById("r3teamnum").textContent = "";
        document.getElementById("b1teamnum").textContent = "";
        document.getElementById("b2teamnum").textContent = "";
        document.getElementById("b3teamnum").textContent = "";

        console.error("Match key is undefined or Schedule data is missing.");
    }
}


/**
* Get the TBA match key for the configured event and selected match level and match number.
*
* @return A string that represents the TBA event code for any level ( e.g. 2023azva_qm3 = Q3 at AZ East or 2023azgl_f1m2 = Finals 2 at AZ West)
*			or an empty string if the match level is not a recognized one ( e.g. "de" for double elimination)
*/
function getCurrentMatchKey() {
	// This works for all match levels.  The match key conforms to TBAs current standard
	level = getLevel();

	if ( level == "qm" ) {
		return document.getElementById( "input_e" ).value + "_" + level + document.getElementById( "input_m" ).value;
		}
	else if ( level == "sf" ) {
		return document.getElementById( "input_e" ).value + "_" + level + document.getElementById( "input_m" ).value + "m1";
		}
	else if ( level == "f" ) {
		return document.getElementById( "input_e" ).value + "_" + level + "1m" + document.getElementById( "input_m" ).value;
		}
	else {
		return "";
		}
	}


/**
* Get the TBA match information (both alliances) for the specified TBA match key
*
* @param {matchKey} The TBA match code for the currently selected match and event
*
* @return A JS struct with both red and blue alliance information extracted from the schedule.  Or an empty
*			string if there is no schedule data (or the matchKey is bogus)
*/
function getMatch( matchKey ) {
	// This needs to be different than getTeamName() because of how JS stores their data
	if ( matchKey !== undefined ) {
		if ( schedule ) {
			var ret = "";
			Array.from( schedule ).forEach( match => ret = match.key == matchKey ? match.alliances : ret );
			return ret;
		    }
        else {
		    console.error( "No match data available!" );
		    return "";
		    }
		}

	console.error( "No match key provided!" );
	return "";
	}


/**
* Get the match data for the currently selected match
*
* @return A JS struct with both red and blue alliance information extracted from the schedule for the current match selection.
*			OR an empty string if there is no schedule data (or the matchKey is bogus)
*/
function getCurrentMatch() {
	return getMatch( getCurrentMatchKey() );
	}


/**
* Get the team number for the currently selected match and robot position
*
* @return The team number as an integer value (sans the TBA frc prefix)
*/
function getCurrentTeamNumberFromRobot() {
	if ( getRobot() != "" && typeof getRobot() !== 'undefined' && getCurrentMatch() != "" ) {
		if ( getRobot().charAt(0) == "r" ) {
			return getCurrentMatch().red.team_keys[ parseInt( getRobot().charAt(1) ) - 1 ]
			}
		else if ( getRobot().charAt(0) == "b" ) {
			return getCurrentMatch().blue.team_keys[ parseInt( getRobot().charAt(1) ) - 1 ]
			}
		}

	// TODO: We really should return some value like 0 if we have no robot or match number selected yet?
	}


/**
* Update the match/team information on the form to match the inputs that were changed.
*
* @param {event} DOM event notification for a changed element
*/
function updateMatchStart( event ) {
	// If there is no schedule data available, do nothing more
	if ( ! schedule ) {
		console.error( "No match schedule data." );
		return;
		}

    return getAlliances( getCurrentMatchKey() );
	}


/**
* Given the name of some radio list on the page, clear all of the radio buttons so none are checked.  This is a
* utility routine to make clearing multiple radio button lists easier than doing the same work over and over in
* another routine.
*
* @param {listName} The name of a radio button list to clear
*/
function clearRadioList( listName ) {
	var ele = document.getElementsByName( listName );
	for( var i = 0; i < ele.length; i++ )
		ele[ i ].checked = false;
}


/**
 * Take a match level key such as "qm" and convert it to plain text
 * 
 * @param {string} key match level key to be converted to a string
 * @returns The plain text version of the match level key submitted
 */
function levelKeyToString(key) {
	var levelStrings = {
		"qm": "Qual",
		"sf": "Playoff",
		"f": "Final"
	};

	return levelStrings[key];
}


/**
* When the page loads, load in our configuration and then load the team and schedule data
* for the event in the configuration.
*/
window.onload = function () {
    // Load the event configuration data and inject some of it into the DOM for use below
	var ret = configure();

	// If we could load and parse the configuration then lets try to get data from TBA for the event
	if ( ret != -1 ) {
		// Get the eventCode that was injected into the DOM when the configuration was loaded
		var ec = document.getElementById( "input_e" ).value;

		// Asynchronously load the teams for the event from TBA
		getTeams( ec );

		// Asynchronously load the schedule for the event from TBA
		getSchedule( ec );
	}

	// Initialize localStorage
	if (!localStorage.getItem($("#input_ed").val() + "length")) {
		localStorage.setItem($("#input_ed").val() + "length", 0);
	}

	if (!localStorage.getItem($("#input_ed").val() + "unscanned")) {
		localStorage.setItem($("#input_ed").val() + "unscanned", 0);
	}

};

