function sortRows(event) {
  const targetElement = event.target;

  // Is this Ascending or Descending?

  let direction = "ascending";

  if (targetElement.classList.contains("ascending")) {
    direction = "descending";
  } else if (targetElement.classList.contains("descending")) {
    direction = "ascending";
  } else {
    direction = "ascending";
  }

  const tableElement = targetElement.closest("table");

  const thElements = Array.from(
    targetElement.parentElement.querySelectorAll("th"),
  );
  const numColumns = thElements.length;

  // Getting Column Number
  const siblings = [];
  let currentSibling = targetElement.previousElementSibling;

  while (currentSibling) {
    siblings.push(currentSibling);
    currentSibling = currentSibling.previousElementSibling;
  }

  const currentColumnIndex = siblings.length;

  const tableBody = tableElement.querySelector("tbody");
  const tableBodyRows = Array.from(tableBody.querySelectorAll("tr"));

  tableBodyRows.sort((row1, row2) => {
    const value1 = row1.cells[currentColumnIndex].innerText.trim();
    const value2 = row2.cells[currentColumnIndex].innerText.trim();

    if (direction === "ascending") {
      return value1.localeCompare(value2);
    } else {
      return value2.localeCompare(value1);
    }
  });

  tableBodyRows.forEach((row) => tableBody.appendChild(row));

  // Adding Down Arrow
  thElements.forEach((th) => {
    th.classList.remove("ascending");
    th.classList.remove("descending");
  });
  targetElement.classList.add(direction);
}

function getAllElementsInColumnAsArray(tableElement, index) {
  const columnElements = [];

  const allRows = Array.from(
    tableElement.querySelector("tbody").querySelectorAll("tr"),
  );

  allRows.forEach((rowElement, rowIndex) =>
    columnElements.push(rowElement.cells[index].innerText.trim()),
  );

  return columnElements;
}

function addSortingFunctionToTable(tableElement) {
  const allColumnHeaders = Array.from(tableElement.querySelectorAll("th"));

  allColumnHeaders.forEach((colHeader) => {
    colHeader.addEventListener("click", sortRows);
    colHeader.style.cursor = "pointer";
  });
}

function addSortingFunctionToAllTables() {
  console.log("Adding Sort Function to Each Table");

  const allTables = Array.from(document.querySelectorAll("table"));
  allTables.forEach((tableElement) => addSortingFunctionToTable(tableElement));
}

// Adding Sortable Nature to all Tables

addSortingFunctionToAllTables();
