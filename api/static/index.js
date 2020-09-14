function EnableDisable(grade) {
		        var selectedValue = grade.options[grade.selectedIndex].value;
		        var category = document.getElementById("category");
		        category.disabled = selectedValue == 2?false:true;
		        if (!category.disabled) {
		            category.focus();
		        }
		    }
function EnableDisable1(category) {
		        var selectedValue = category.options[category.selectedIndex].value;
		        var course = document.getElementById("course");
		        course.disabled = selectedValue == "creative"?false:true;
		        if (!course.disabled) {
		            course.focus();
		        }
		    }
function EnableDisableTiming(batch) {
		        var selectedValue = batch.options[batch.selectedIndex].value;
		        var timing = document.getElementById("timing");
		        timing.disabled = selectedValue == "mwf"?false:true;
		        if (!timing.disabled) {
		            timing.focus();
		        }
		    }

function EnableDisableBtop() {
	var selectedValue = timing.options[timing.selectedIndex].value;
	var x = document.getElementById("btop");
	x.disabled = selectedValue == "eve"?false:true;
	  if (!x.disabled) {
	    x.style.display = "block";
	    x.focus();
	  } else {
	    x.style.display = "none";
	  }
}