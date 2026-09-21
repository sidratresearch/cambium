import { addSortingFunctionToAllTables } from "./tableSorting.js";
import {
  cambiumInitializeLightDark,
  cambiumToggleLightDark,
} from "./lightDark.js";

// Adding Sortable Nature to all Tables
addSortingFunctionToAllTables();

// Runs on Initialization
cambiumInitializeLightDark();
