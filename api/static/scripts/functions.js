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
    updateHiddenInput(); // Update the hidden input when removing an item
  });

  // Append the remove button to the list item
  listItem.appendChild(removeButton);

  // Append the list item to the selected list
  selectedList.appendChild(listItem);

  // Clear the input field
  document.getElementById("genre").value = "";

  updateHiddenInput(); // Update the hidden input when adding an item
}

// Event listener for when an option is selected
document.getElementById("genre").addEventListener("change", addToSelectedList);

// Function to update the hidden input with selected genres
function updateHiddenInput() {
  var selectedGenres = getSelectedGenres();
  document.getElementById("selectedGenres").value = selectedGenres.join(", ");
}

// Function to get selected genres from the list
function getSelectedGenres() {
  var selectedGenres = [];
  var selectedOptions = document.getElementById("selectedList").getElementsByTagName("li");

  for (var i = 0; i < selectedOptions.length; i++) {
    var genreText = selectedOptions[i].innerText.trim();
    genreText = genreText.endsWith("Remove") ? genreText.slice(0, -"Remove".length) : genreText;
    selectedGenres.push(genreText);
  }

  return selectedGenres;
}
