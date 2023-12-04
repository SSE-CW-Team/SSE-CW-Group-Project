// script.js



// Function to filter options based on user input
function filterOptions() {
  updateLikedSongsValue();
  var input = document.getElementById("genre").value.toLowerCase();
  var options = document.getElementById("genreList").getElementsByTagName("option");

  for (var i = 0; i < options.length; i++) {
    var optionValue = options[i].value.toLowerCase();
    if (optionValue.startsWith(input)) {
        options[i].setAttribute("data-match", "true");
    } else {
        options[i].removeAttribute("data-match");
    }
  }

  // Remove non-matching options from the list
  var nonMatchingOptions = datalist.querySelectorAll("option:not([data-match])");
  nonMatchingOptions.forEach(function (option) {
      option.remove();
  });
}
function updateLikedSongsValue() {
  var slider = document.getElementById("liked_songs");
  var valueDisplay = document.getElementById("liked_songs_value");
  var steppedValue = Math.round(slider.value / 20) * 20; // Round to the nearest multiple of 20
  valueDisplay.innerHTML = steppedValue;
}
// Function to add selected option to the list
function addToSelectedList() {
  var inputElement = document.getElementById("genre");

  // Check if the input box is empty
  if (inputElement.value.trim() === "") {
    return; // Exit early if there is no text
  }
  var selectedItem = inputElement.value.trim().toLowerCase();
  var dropdownOptions = document.getElementById("genreList").getElementsByTagName("option");

  // Filter dropdown options based on user input
  var filteredOptions = Array.from(dropdownOptions).filter(
    (option) => option.value.toLowerCase() === selectedItem
  );

  if (filteredOptions.length === 0) {
    return; // Exit early if there are no filtered options
  }

  // Check if there are matching options in the filtered list
  var matchingOption = filteredOptions.length > 0 ? filteredOptions[0] : null;

  // If there is no match in the filtered list, use the top value from the original dropdown
  if (!matchingOption && dropdownOptions.length > 0) {
    matchingOption = dropdownOptions[0];
  }

  // Add the selected option to the list
  addOptionToSelectedList(matchingOption.value);

  // Clear the input field
  inputElement.value = "";
}

// Event listener for keydown event on the input field
document.getElementById("genre").addEventListener("keydown", function (event) {
  if (event.key === "Enter") {
    // Prevent the default behavior of the Enter key
    event.preventDefault();
    addToSelectedList(); // Simulate a click on the most relevant value
  }
  console.log(selectedList)
});

// Function to add the selected option to the list
function addOptionToSelectedList(selectedItem) {
  var selectedList = document.getElementById("selectedList");
  var listItem = document.createElement("li");
  listItem.textContent = selectedItem;

  // Create a remove button
  var removeButton = document.createElement("button");
  removeButton.textContent = "Remove";
  removeButton.classList.add("remove");
  removeButton.addEventListener("click", function () {
    var removedGenre = listItem.textContent.trim();
    listItem.remove();
    updateHiddenInput(); // Update the hidden input when removing an item
    addOptionBackToDropdown(removedGenre); // Add the removed option back to the dropdown
  });

  // Append the remove button to the list item
  listItem.appendChild(removeButton);

  // Find the correct position to insert the new item in alphabetical order
  var existingItems = selectedList.getElementsByTagName("li");
  var insertIndex = 0;

  for (var i = 0; i < existingItems.length; i++) {
    var existingItemText = existingItems[i].textContent.trim();
    if (selectedItem.toLowerCase() > existingItemText.toLowerCase()) {
      insertIndex = i + 1;
    } else {
      break;
    }
  }

  // Insert the new item at the correct position
  if (insertIndex < existingItems.length) {
    selectedList.insertBefore(listItem, existingItems[insertIndex]);
  } else {
    selectedList.appendChild(listItem);
  }

  // Remove the selected genre from the dropdown list
  removeOptionFromDropdown(selectedItem);

  updateHiddenInput(); // Update the hidden input when adding an item

  printSelectedListState();
}

function toggleAdvancedOptions() {
  var advancedSearchContainer = document.getElementById("advanced-search-container");
  var advancedSearchCheckbox = document.getElementById("advanced-search-checkbox");

  // Toggle the display of the advanced search container based on the checkbox state
  advancedSearchContainer.style.display = advancedSearchCheckbox.checked ? "block" : "none";
}

// Function to print the current state of the selected list to the console
function printSelectedListState() {
  var selectedGenres = getSelectedGenres();
  console.log("Selected List State:", selectedGenres);
}


// Function to remove the selected option from the dropdown list
function removeOptionFromDropdown(optionText) {
  var dropdownOptions = document.getElementById("genreList").getElementsByTagName("option");
  for (var i = 0; i < dropdownOptions.length; i++) {
    if (dropdownOptions[i].value.toLowerCase() === optionText.toLowerCase()) {
      dropdownOptions[i].remove();
      break;
    }
  }
}

// Function to add the removed option back to the dropdown list at the correct alphabetical spot
function addOptionBackToDropdown(optionText) {
  var dropdownOptions = document.getElementById("genreList").getElementsByTagName("option");
  for (var i = 0; i < dropdownOptions.length; i++) {
    if (optionText.toLowerCase() < dropdownOptions[i].value.toLowerCase()) {
      var newOption = document.createElement("option");
      optionText = optionText.endsWith("Remove") ? optionText.slice(0, -"Remove".length) : optionText;
      newOption.value = optionText;
      dropdownOptions[i].parentNode.insertBefore(newOption, dropdownOptions[i]);
      break;
    }
  }
  // If the option should be added at the end
  if (i === dropdownOptions.length) {
    var newOption = document.createElement("option");
    optionText = optionText.endsWith("Remove") ? optionText.slice(0, -"Remove".length) : optionText;
    newOption.value = optionText;
    document.getElementById("genreList").appendChild(newOption);
  }
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
