/*
	JQuery functions to enable various interactions in profile.html
	Author: Gaetano Pressimone
	Last Modified: Aug 13, 2012
*/

/*
makes sure the page is loaded before using and dont load mouseover_table fn
 if a mobile device
*/
$(document).ready(function() {
  $("button.edit").click(on_edit_button_click);
  show_keyform();
  show_api_key();
  if (!(navigator.userAgent.match(/(iphone|ipod|ipad|android|blackberry|windows ce|palm|symbian)/i))) {
  mouseover_table();}
});
/*
When a Edit button is pushed, the cell's hidden content is revealed and hides 
all other table cells content (if previously revealed).  Also changes the text of 
the edit button from "Edit' to "Cancel" and vice versa.
*/
function on_edit_button_click(){
		if ($(this).text()=='Edit'){
			$("#middle").find("button.edit").text('Edit')
				.siblings('span').hide()
				.siblings('span.value').show();

			$(this).siblings('span').show()
		 			  .siblings('span.value').hide();
			$(this).text('Cancel');
		} else {
			$(this).siblings('span').hide().siblings('span.value').show();
			$(this).text('Edit');
		}
}

/*
When the upload button is pushed, the upload pubkey form and cancel button
are shown while the download button is hidden.
When the cancel button is pushed the upload pubkey form and cnacel button
are hidden and the download button is shown. 
*/
function show_keyform(){
	$("button#show_keyform").click(function(){
		$(this).hide()
					.siblings('span').show()
					.siblings('span.value').hide();
		$('button.download').hide();
	});
  $("button.cancel").click(function(){
		$("button#show_keyform").siblings('span').hide()
					 			.siblings('span.value').show();
		$('button.download,button#show_keyform').show();
	});
}
/*
show/hide the api key when double clicked 
*/
function show_api_key(){
	$("span.api_cell").dblclick(function(){
		$("#api_key").show();
		$(this).hide();
	});				   
	$("span#api_key").dblclick(function(){
		$("span.api_cell").show();
		$(this).hide();
	});
}
/*
shows the "?" help img tooltip in the table row on mouseover and hides it
when mouse leaves row 
*/
function mouseover_table(){
  $(".profile tr").not(':first').hover(
		function () {
			$(this).contents().find("img.help").show();	
		}, 
 		function () {
			$(this).find("img.help:last").hide();
		}
	);
}
