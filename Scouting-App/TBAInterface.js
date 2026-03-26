// TBAInterface funcitons to pull data from TheBlueAlliance.com
//
// Slightly reformatted from the original source to add comments.  The TBA key is the
// original one from ScoutingPASS.  We really should get our own but thats something to do
// AFTER the bigger changes are added to our scouting app.

// The teams at the selected event
var teams = null;

// The match schedule at the selected event
var schedule = null;

// The TBA API key to use when making TBA API calls
var authKey = "uTHeEfPigDp9huQCpLNkWK7FBQIb01Qrzvt4MAjh9z2WQDkrsvNE77ch6bOPvPb6";

/**
* Get list of teams at the event
*
* @param {eventCode} - The TBA event code (i.e. 2024azva) to pull the team list for
*/
function getTeams( eventCode ) {
	// Request the team list if we have an API key.
	if ( authKey ) {
		var xmlhttp = new XMLHttpRequest();
		var url = "https://www.thebluealliance.com/api/v3/event/" + eventCode + "/teams/simple";

		xmlhttp.open( "GET", url, true );
		xmlhttp.setRequestHeader( "X-TBA-Auth-Key", authKey );
		xmlhttp.onreadystatechange = function() {
			// State 4 means that the request had been sent, the server had finished returning the response and 
			// the browser had finished downloading the response content. Basically the AJAX call has completed.
			if ( this.readyState == 4 ) {
                const loadedTeamsIcon = document.getElementById( "loaded_teams" );

                if ( this.status == 200 ) {
                    // Team info loaded successfully!
				    var response = this.responseText;
				    teams = JSON.parse( response );

                    // Twiddle the Teams info icon accordingly
                    if ( loadedTeamsIcon ) {
                        loadedTeamsIcon.classList.remove( "fa-xmark" );
                        loadedTeamsIcon.classList.add( "fa-check" );
                    }
                }
                else {
                    // Error loading the team info so twiddle the Teams info icon accordingly
                    if ( loadedTeamsIcon ) {
                        loadedTeamsIcon.classList.remove( "fa-xmark" );
                        loadedTeamsIcon.classList.add( "fa-exclamation" );
                    }

                    console.error( "Error fetching teams:", this.status );
                }
 			}
		};
		// Send request
		xmlhttp.send();
	}
}

/**
* Get schedule for the specified event
*
* @param {eventCode} - The TBA event code (i.e. 2024azva) to pull the schedule for
*/
function getSchedule( eventCode ) {
	// Request the team list if we have an API key.
	if ( authKey ) {
		var xmlhttp = new XMLHttpRequest();
		var url = "https://www.thebluealliance.com/api/v3/event/" + eventCode + "/matches/simple";
		
		xmlhttp.open( "GET", url, true );
		xmlhttp.setRequestHeader( "X-TBA-Auth-Key", authKey );
		xmlhttp.onreadystatechange = function() {
			// State 4 means that the request had been sent, the server had finished returning the response and 
			// the browser had finished downloading the response content. Basically the AJAX call has completed.
			if ( this.readyState == 4 ) {
                const loadedSchedIcon = document.getElementById( "loaded_sched" );

                if ( this.status == 200 ) {
                    // Schedule info loaded successfully!
				    var response = this.responseText;
				    schedule = JSON.parse( response );

                    // Twiddle the Teams info icon accordingly
                    if ( loadedSchedIcon ) {
                        loadedSchedIcon.classList.remove( "fa-xmark" );
                        loadedSchedIcon.classList.add( "fa-check" );
                    }
			    }
                else {
                    // Error loading the schedule info so twiddle the schedule icon accordingly
                    if ( loadedSchedIcon ) {
                        loadedSchedIcon.classList.remove( "fa-xmark" );
                        loadedSchedIcon.classList.add( "fa-exclamation" );
                    }

                    console.error( "Error fetching the schedule:", this.status );
                }
            }
		};
		// Send request
		xmlhttp.send();
	}
}
