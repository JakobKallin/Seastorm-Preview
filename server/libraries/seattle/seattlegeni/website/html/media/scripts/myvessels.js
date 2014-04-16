$(document).ready(toggle_detail);
$(document).ready(get_resources_loading_indicator);

function toggle_detail() {
	$("#expand").click(function () {
		$("#action_detail").toggle();
		if ($(this).text() == "[+]") {
			$(this).text("[-]");
		} else {
			$(this).text("[+]");
		}
	});
}

function get_resources_loading_indicator() {
	$("#getresources > form").submit(function () {
		$("#getresources > form > input[type='submit']").attr('disabled', 'disabled');
		$("#loading_indicator").css('visibility', 'visible'); 
	});
}
