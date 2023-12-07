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
  var genres_text = document.getElementById("selectedGenresText");
  genres_text.innerHTML = "Selected genres:";
  var inputElement = document.getElementById("genre");

  // Check if the input box is empty
  if (inputElement.value.trim() === "") {
    return; // Exit early if there is no text
  }
  var selectedItem = inputElement.value.trim().toLowerCase();
  var dropdownOptions = document.getElementById("genreList").getElementsByTagName("option");

  // Filter dropdown options based on user input
  var filteredOptions = Array.from(dropdownOptions).filter((option) => option.value.toLowerCase() === selectedItem);

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
  console.log(selectedList);
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

// Existing JavaScript functions remain unchanged

// Function to update default values based on selected workout
function updateDefaultValues(workout) {
  var tempo = 0;
  var runLength = 0;
  var danceability = 0.5;
  var energy = 0.5;
  var defaultGenres = [];

  // Set default values based on the selected workout
  switch (workout) {
    case "running":
      tempo = 90;
      danceability = 0.7;
      energy = 0.6;
      defaultGenres = ["Pop", "Rock", "Electronic"];
      break;
    case "boxing":
      tempo = 130;
      danceability = 0.5;
      energy = 0.9;
      defaultGenres = ["Hip-Hop", "Rock", "Electronic"];
      break;
    case "cycling":
      tempo = 140;
      danceability = 0.3;
      energy = 0.7;
      defaultGenres = ["EDM", "Rock", "Pop"];
      break;
    case "yoga":
      tempo = 60;
      danceability = 0.1;
      energy = 0.2;
      defaultGenres = ["Ambient", "Classical", "Instrumental"];
      break;
    case "gym":
      tempo = 100;
      danceability = 0.5;
      energy = 0.6;
      defaultGenres = ["Metal", "Rock", "Electronic"];
      break;
    case "general":
      tempo = 100;
      danceability = 0.5;
      energy = 0.5;
      break;
  }

  // Update default values in the form
  document.getElementById("tempo").value = tempo;
  document.getElementById("danceability").value = danceability;
  document.getElementById("energy").value = energy;

  updateTempoValue();
  handleWorkoutSelection(workout);

  // Update genres in the selected list
  updateGenresList(defaultGenres);
}

// Function to update the genres list based on selected default genres
function updateGenresList(defaultGenres) {
  // Clear existing selected genres
  clearSelectedGenres();

  // Add default genres to the selected list
  defaultGenres.forEach(function (genre) {
    addOptionToSelectedList(genre);
  });

  // Update the hidden input with selected genres
  updateHiddenInput();
}

// Function to clear the selected genres list
function clearSelectedGenres() {
  var selectedList = document.getElementById("selectedList");
  selectedList.innerHTML = "";
}

// Function to get a random integer within a range

// Event listener for changes in the workout selection
document.getElementsByName("workout").forEach(function (radio) {
  radio.addEventListener("change", function () {
    updateDefaultValues(this.value);
  });
});

// Assuming you have a function to handle workout selection
function handleWorkoutSelection(workoutType) {
  // Remove existing workout class from body
  document.body.classList.remove("running", "boxing", "cycling", "yoga", "gym", "general");

  // Add the selected workout class to body
  document.body.classList.add(workoutType);
  updateh1s(workoutType);
  updateSliderColors(workoutType);
}

function updateh1s(workoutType) {
  const h1Element = document.querySelector("h1");
  let color;

  switch (workoutType) {
    case "running":
      color = "#39ff14";
      break;
    case "boxing":
      color = "#8a2be2";
      break;
    case "cycling":
      color = "#00bfff";
      break;
    case "yoga":
      color = "#ffff00";
      break;
    case "gym":
      color = "#ff3e3e";
      break;

    default:
      color = "#ffffff";
  }

  h1Element.style.color = color;
}

function updateSliderColors(workoutType) {
  const sliders = document.querySelectorAll('input[type="range"]');
  let backgroundColor;

  switch (workoutType) {
    case "running":
      backgroundColor = "linear-gradient(to right, #00b300, #39ff14)";
      break;
    case "boxing":
      backgroundColor = "linear-gradient(to right, #4b0082, #8a2be2)";
      break;
    case "cycling":
      backgroundColor = "linear-gradient(to right, #001f3f, #00BFFF)";
      break;
    case "yoga":
      backgroundColor = "linear-gradient(to right, #b3b300, #ffff00)";
      break;
    case "gym":
      backgroundColor = "linear-gradient(to right, #cc0000, #ff3e3e)";
      break;

    default:
      backgroundColor = "linear-gradient(to right,  #d9d9d9, #ffffff)";
  }

  sliders.forEach((slider) => {
    slider.style.background = backgroundColor;
  });
}
