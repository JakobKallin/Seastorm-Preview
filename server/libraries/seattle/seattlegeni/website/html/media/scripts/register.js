/*
	Edited by: Gaetano Pressimone
	Last Modfied: Sept 20 2012
*/
$(document).ready(function() {
	toggle_upload();
	get_resources_loading_indicator();
	$("#id_gen_upload_choice").change(toggle_upload);
});

function toggle_upload() {
	if ($("#id_gen_upload_choice").val() == "1") {
		$("#uploadkey").hide();
	} else {
		$("#uploadkey").show();
	}
}
/* Disables submit button on press and shows the loading icon */
function get_resources_loading_indicator() {
	$("#middle > form").submit(function () {
		$('input:submit').attr("disabled", true);
		$("#loading_indicator").css('visibility', 'visible');
	});
}