/*
	Created by: Gaetano Pressimone Sept 20 2012
*/
$(document).ready(get_resources_loading_indicator);
/* Disables submit button on press and shows the loading icon */
function get_resources_loading_indicator() {
  $("#middle > form").submit(function () {
		$('input:submit').attr("disabled", true);
      $("#loading_indicator").css('visibility', 'visible');
  });
}
