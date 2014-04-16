/*
	JavaScript to enable interactions in mygeni.html
	Author: Sean (Xuanhua) Ren
	Last Modified: 4/9/2009
*/


/*
	load the credits and shares when the page is ready
*/
$(document).ready(function() {
	update_credits();
	update_shares();
});



/*
	Create a block with given username and width for credits or shares
	and return the block
	If width is less than 10%, create and append to a "Other" block
	
	username: the username for the block
	width: the width of the block
	isShare: true if it's in the "shares" bar, false if it's in the "credits" bar
	
	return: the block created
*/
function create_block(username, width, isShare) {
	var block = $(document.createElement('td'));
	block.css({
		'width': width + '%',
		'background-color': '#' + color_generator(username)
	});
	var percent = $(document.createElement('span'));
	percent.text(width + '%');

	if (isShare) {
		block.attr("id", "usage" + username);
		if (username == "Free" && width > 0) {
			var get = $(document.createElement('a'));
			get.attr('id','getresourcesbutton');
			get.attr('href', 'myvessels');
			get.text('get');
			// get.click(get_resources_dialog);
			block.append(get);
			
			var share = $(document.createElement('a'));
			share.attr('id','shareresourcesbutton');
			share.attr('href','#');
			share.text('share');
			share.click(share_resources_dialog);
			block.append(share);
			
		} else if (username != "Me" && username != "Others" && username != "Free") {
			/* we only want to end up here if the block is a share with another user */
			var close = $(document.createElement('a'));
			close.attr('href','#');
			close.text('x');
			close.click(function() {
				$.post("../control/ajax_editshare",
						{ username: username, percent: 0 },
						function (data) {
							var json = eval('(' + data + ')');
							if (json.success) {
								update_shares();
							} else {
								alert(json.error);
							}
						});
			});
			block.append(close);
			percent.attr("title", "Click to change percent");
			percent.tooltip({cssClass:"tooltip"});
			percent.css("cursor", "pointer");
			percent.css("text-decoration", "underline");
			percent.click(function() {
				change_percent(username, width);
			});
		}
	}
	
	if (username == "Others") {
		percent.attr("title", "Click to reveal");
		percent.tooltip({cssClass:"tooltip"});
		percent.css("cursor", "pointer");
		percent.css("text-decoration", "underline");
		percent.click(function () { toggle_table(isShare) });
		// block.attr("id", "creditOthers");
	}
	block.append(percent);
	return block;
}


/*
	Create a name label with given width for shares or credits bar
	
	username: the username for the label
	width: the width for the label
	isShare: true if it is in "shares" bar and false if it is in "credits" bar
	
	return: the label created
*/
function create_label(username, width, isShare) {
	var label = $(document.createElement('td'));
	if (isShare) {
		label.attr("id", "labelusage" + username);
	}
	label.text(username);
	label.css({
		'width': width + '%'
	});
	return label;
}


/*
	Append the given username and percent to "Others" table
	
	type: type of the table, "credits" or "shares"
	username: username to added to the table
	percent: percent shown in the table
*/
function add_other(type, username, percent) {
	var table;
	if (type == "credits") {
		table = $("#creditotherstable");
	} else if (type == "shares") {
		table = $("#usageotherstable");
	}
	var tr = $(document.createElement("tr"));
	tr.html("<td>" + username + "</td><td>" + percent + "</td>");
	if (type == "shares") {
		var control = $(document.createElement("td"));
		var edit = $(document.createElement("button"));
		edit.text("Edit");
		edit.click(function() {
			change_percent(username, percent);
		});
		var close = $(document.createElement("button"));
		close.text("Delete");
		close.click(function() {
			$.post("../control/ajax_editshare",
					{ username: username, percent: 0 },
					function(data) {
						var json = eval('(' + data + ')');
						if (json.success) {
							update_shares();
						} else {
							alert(json.error);
						}
					});
			tr.remove();
		});
		control.append(edit);
		control.append(close);
		tr.append(control);
	}
	table.append(tr);
}


/*
	Display the "Change Percent" modal dialog box
	
	username: username of the editing block
	current_percent: current percent of the block editing
*/
function change_percent(username, current_percent) {
	var dialog = $(document.createElement("div"));
	dialog.attr("id", "changepercentdialog");
	dialog.html('<h3>Change Percent</h3>');
	var input = $(document.createElement("input"));
	input.attr("type", "text");
	input.val(current_percent);
	input.click(function () { $(this).val("") });
	var symbol = $(document.createElement("span"));
	symbol.html(" %<br />");
	var cancel = $(document.createElement("button"));
	cancel.text("Cancel");
	var save = $(document.createElement("button"));
	save.text("Save");
	cancel.click(function () {
		close_dialog();
		$(this).parent().remove();
	});
	save.click(function() {
		var new_percent = parseInt(input.val());
		//if (validate(current_percent, new_percent)) {		
		save_percent(username, new_percent);
		//}
	});
	dialog.append(input);
	dialog.append(symbol);
	dialog.append(cancel);
	dialog.append(save);
	$("#dialogframe").append(dialog);
	$("#dialogframe").fadeIn("fast");
	$("#overlay").fadeIn("fast");
	$("#changepercentdialog").fadeIn("fast");
}


/*
	Save the percent of the the block when click "save" on the
	change_percent dialog box
	
	username: username of the block
	percent: new percent of the block user enters
*/
function save_percent(username, percent) {
	$.post("../control/ajax_editshare",
			{ username: username, percent: percent },
			function (data) {
				var json = eval(data);
				if (json.success) {
					$("#changepercentdialog").remove();
					$("#dialogframe").hide();
					$("#overlay").hide();
					update_shares();
				} else {
					create_warning(json.error, $("#changepercentdialog h3"));
				}
	   		},
			"json");
}


/*
	Toggle display "Others" table
	
	isShare: true if the table to toggle is in "shares"
			 false if the table to toggle is in "credits"
*/
function toggle_table(isShare) {
	if (isShare) {
		$("#usageotherstable").toggle();
	} else {
		$("#creditotherstable").toggle();
	}
}


/*
	Display the "Get Resources" modal dialog
	Currently disabled because the button directly linked to myVessels page
*/
function get_resources_dialog() {
	$("#dialogframe").fadeIn("fast");
	$("#overlay").fadeIn("fast");
	$("#getresourcesdialog").fadeIn("fast");
	$(".cancel").click(close_dialog);
	$("#getresourcesaction").click(get_resources);
}


/*
	Display the "Share Resources" modal dialog
*/
function share_resources_dialog() {
	$("#shareresourcesdialog #username").val("");
	$("#shareresourcesdialog #percent").val("");
	$("#dialogframe").fadeIn("fast");
	$("#overlay").fadeIn("fast");
	$("#shareresourcesdialog").fadeIn("fast");
	$(".cancel").click(close_dialog);
	if ($("#shareresourcesdialog .warning")) {
	    $("#shareresourcesdialog .warning").remove();
	}
	$("#shareresources").click(function () {
		var username = $("#shareresourcesdialog #username").val();
		var percent = parseInt($("#shareresourcesdialog #percent").val());
		// if (validate(0, percent)) {
		share_resources(username, percent);
		//} 
	});
}


/*
	Hide the modal dialog currently being displayed
*/
function close_dialog() {
    if ($(this).parent().children(".warning")) {
		$(this).parent().children(".warning").remove();
    }
	$(this).parent().hide();
	$("#dialogframe").hide();
	$("#overlay").hide();
}


/*
	Validate the returned data before displaying
	
	url: url for posting ajax
	args: arguments for posting ajax
	func: function to callback when server returns data
*/
function post_ajax(url, args, func) {
	$.post(url, args, function(data) {
		// check data
		// if data ok then:
		func(data)
		// else:
		// display content as raw html in a new popup
	});
}


/*
	Save the given amount of resources with given user
	
	username: username of the user to be shared
	percent: percent of resources to share
*/
function share_resources(username, percent) {
	post_ajax("../control/ajax_createshare",
			{ username: username, percent: percent },
			function(data) {
				var json = eval('(' + data + ')');
				if (json.success) {
					$("#shareresourcesdialog").hide();
					$("#dialogframe").hide();
					$("#overlay").hide();
					update_shares();
				} else {
					create_warning(json.error, $("#shareresourcesdialog h3"));
				}
			});
}


/*
	Get the amount of resources taken from the "Get Resources" dialog
	Currently disabled because the button directly linked to myVessels page
*/
function get_resources() {
	var numvessels = parseInt($("#numvessels").val());
	var env = parseInt($("#environment").val());
	if ($("#getresourcesdialog .warning")) {
	    $("#getresourcesdialog .warning").remove();
	}
	$.post("../control/ajax_getvessels",
			{ num: numvessels, env: env },
			function (data) {
				var json = eval('(' + data + ')');
				// alert(json.mypercent);
				// alert(json.success);
				if (json.success) {
					$("#getresourcesdialog").hide();
					$("#dialogframe").hide();
					$("#overlay").hide();
					update_shares();
				} else {
					create_warning(json.error, $("#getresourcesdialog h3"));
				}
			});
}


/*
	Create and append a warning sign after the given position
	
	error: the error message to show in the html
	position: the location where the error message should append to
*/
function create_warning(error, position) {
	var warning = $(document.createElement("p"));
	warning.html(error);
	warning.addClass("warning");
	warning.insertAfter(position);
}


/*
	Generate a color in hex notation for a username, which assigns different
	colors to different usernames.
	
	username: username for generating random colors
	
	return: hex representation of the color
*/
function color_generator(username) {
	var seeds = ['cc','ff'];
	var color = seeds[username.charCodeAt(0) % 2] +
				seeds[username.charCodeAt(1) % 2] +
				seeds[username.charCodeAt(username.length - 1) % 2];
	if (color == "ffffff") {
		color = "ffffcc";
	} else if (color == "cccccc") {
		color = "ccccff";
	}
	if (username == "Free") {
		color = "ffffff";
	} else if (username == "Me") {
		color = "cccccc";
	}
	return color;
}


/*
	Load all blocks in "credits" bar
	If it takes more than 15000 milliseconds, display message to let user refresh the page
*/
function update_credits() {
	var loading = true;
	setTimeout(function () {
		if (loading) {
			$("#credits").html("<td><img src='../media/images/loadingbar.gif' alt='loading' /></td>");
		}
	}, 3000);
	setTimeout(function () {
		if (loading) {
			$("#credits").html("<td>The information is taking too long to load. Try refreshing the page and contact us if you have further problems.</td>");
		}
	}, 15000);
	$.post("../control/ajax_getcredits",
			function (data) {
				loading = false;
				$("#credits").empty();
				$("#creditnames").empty();
				$("#creditotherstable tr:gt(0)").empty();
				var json = eval('(' + data + ')');
				var total_others = 0;
				for (var i = 0; i < json[0].length; i++) {
					add_cell("credits", json[0][i].username, json[0][i].percent);
				}
				for (var i = 0; i < json[1].length; i++) {
					add_other("credits", json[1][i].username, json[1][i].percent);
					total_others += json[1][i].percent;
				}
				if (total_others > 0) {
					add_cell("credits", "Others", total_others);
				}
				add_cell("credits", json[2][0].username, json[2][0].percent);
				$("#vesselscredits").text(json[3] + " vessels credits");
				$("#creditotherstable tr:odd").addClass("odd");
				$("#creditotherstable tr:even").addClass("even");
			}, 
			"json");
}


/*
	Load all blocks in "shares" bar
	If it takes more than 15000 milliseconds, display message to let user refresh the page
*/
function update_shares() {
	loading = true;
	setTimeout(function () {
		if (loading) {
			$("#usage").html("<td><img src='../media/images/loadingbar.gif' alt='loading' /></td>");
		}
	}, 3000);
	setTimeout(function () {
		if (loading) {
			$("#usage").html("<td>The information is taking too long to load. Try refreshing the page and contact us if you have further problems.</td>");
		}
	}, 15000);
	$.post("../control/ajax_getshares",
			function (data) {
				loading = false;
				$("#usage").empty();
				$("#usagenames").empty();
				$("#usageotherstable tr:gt(0)").empty();
				var json = eval('(' + data + ')');
				var total_percent = 0;
				var total_others = 0;
				for (var i = 0; i < json[0].length; i++) {
					add_cell("shares", json[0][i].username, json[0][i].percent);
					total_percent += json[0][i].percent;
				}
				for (var i = 0; i < json[1].length; i++) {
					add_other("shares", json[1][i].username, json[1][i].percent);
					total_others += json[1][i].percent;
				}
				total_percent += total_others + json[2][0].percent;
				if (total_others > 0) {
					add_cell("shares", "Others", total_others);
				} else {
					$("#usageotherstable").hide();
				}
				add_cell("shares", json[2][0].username, json[2][0].percent);
				add_cell("shares", "Free", 100 - total_percent);
				$("#vesselsavailable").text(json[3] + " vessels available");
				update_numvessels(json[3]);
				$("#usageotherstable tr:odd").addClass("odd");
				$("#usageotherstable tr:even").addClass("even");
			},
			"json");
}


/*
	Add a block-label pair to a perticular bar
	
	type: "credits" if adding to the "credits" bar
		  "shares" if adding to the "shares" bar
	username: username of the cell to add
	percent: percent of the cell to add
*/
function add_cell(type, username, percent) {
	if (type == "credits") {
		var block = create_block(username, percent, false);
		var label = create_label(username, percent, false);
		$("#credits").append(block);
		$("#creditnames").append(label);
	} else if (type == "shares") {
		var block = create_block(username, percent, true);
		var label = create_label(username, percent, true);
		$("#usage").append(block);
		$("#usagenames").append(label);
	}
}


/*
	Let the select box in "Get Resources" dialog display possible number of vessels
	
	number: number of possible vessels to get
*/
function update_numvessels(number) {
	$("#numvessels").empty();
	for (var i = 1; i <= number; i++) {
		var option = $(document.createElement("option"));
		option.val(i);
		option.text(i);
		$("#numvessels").append(option);
	}
}
