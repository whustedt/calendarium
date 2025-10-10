# Milestone Tracking Feature

## Overview

The milestone tracking feature automatically identifies and visually highlights significant anniversaries for recurring events in the Calendarium timeline. This feature enhances the user experience by celebrating important milestones while maintaining the simplicity of the single date input field.

## Features

### Automatic Milestone Detection

- **Original Start Year Tracking**: When creating a recurring event (category with `repeat_annually=True`), the system automatically captures the year from the date entered.
- **Smart Calculation**: Milestones are calculated based on the difference between the current year and the original start year.
- **Significant Anniversaries**: The following anniversaries are automatically recognized as milestones:
  - 1st anniversary
  - Every 5th year up to 25th (5th, 10th, 15th, 20th, 25th)
  - Every 25th year after 25th (50th, 75th, 100th, etc.)

### Visual Highlighting

Milestone events are prominently displayed in the timeline with:
- **Golden Border**: A 3px gold border to make them stand out
- **Golden Shadow**: A glowing shadow effect (20px blur with gold color)
- **Milestone Badge**: A badge at the top center showing the milestone type (e.g., "🎊 5th", "🎊 10th")

### User Experience

- **No UI Changes Required**: Users continue to enter dates using the existing single date input field
- **Automatic Processing**: The system handles all milestone tracking logic automatically
- **Backwards Compatible**: Existing entries without `original_start_year` continue to work normally
- **Non-Intrusive**: Non-milestone events display normally without any special styling

## Usage

Simply create an entry with a recurring category:

1. Select a recurring category (e.g., "Birthday")
2. Enter the date (e.g., "2020-05-15")
3. Enter title and description
4. Submit

The system automatically sets `original_start_year` and calculates milestones for future occurrences.

## Testing

Run milestone tests with:
```bash
pytest tests/test_milestones.py -v
```

## Migration

Apply the database migration:
```bash
flask db upgrade
```
