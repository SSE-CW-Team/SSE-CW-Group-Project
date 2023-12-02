// script.js

// Function to filter options based on user input
function filterOptions() {
  var input = document.getElementById("genre").value.toLowerCase();
  var options = document.getElementById("genreList").getElementsByTagName("option");
  for (var i = 0; i < options.length; i++) {
    var optionValue = options[i].value.toLowerCase();
    if (optionValue.indexOf(input) === -1) {
      options[i].setAttribute("hidden", true);
    } else {
      options[i].removeAttribute("hidden");
    }
  }
}

// Function to add selected option to the list
function addToSelectedList() {
  var selectedItem = document.getElementById("genre").value;
  var selectedList = document.getElementById("selectedList");
  var listItem = document.createElement("li");
  listItem.textContent = selectedItem;

  // Create a remove button
  var removeButton = document.createElement("button");
  removeButton.textContent = "Remove";
  removeButton.classList.add("remove");
  removeButton.addEventListener("click", function () {
    listItem.remove();
  });

  // Append the remove button to the list item
  listItem.appendChild(removeButton);

  // Append the list item to the selected list
  selectedList.appendChild(listItem);

  // Clear the input field
  document.getElementById("genre").value = "";
}

// Event listener for when an option is selected
document.getElementById("genre").addEventListener("change", addToSelectedList);
