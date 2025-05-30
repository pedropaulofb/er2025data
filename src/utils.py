# Utility function to save to CSV
import gzip
import os
import pickle
from typing import Optional, Union

import pandas as pd
from loguru import logger


def color_text(texts):
    """Function to color specific original_labels for legends or axis labels."""
    for text in texts:
        if 'none' in text.get_text():
            text.set_color('#d943d6')
        elif 'other' in text.get_text():
            text.set_color('red')


def bold_left_labels(texts, red_line_index):
    """
    Function to apply bold font to x-axis labels that are on or to the left of the red line.

    :param texts: List of x-axis label original_labels.
    :param red_line_index: The index where the red line is drawn.
    """
    for i, text in enumerate(texts):
        if i <= red_line_index:
            text.set_fontweight('bold')


def append_chars_to_labels(texts, data_occurrence, data_groupwise, median_occurrence, median_groupwise):
    """
    Function to append characters to x-axis labels based on occurrence-wise and group-wise frequencies.

    :param data_occurrence: DataFrame containing occurrence-wise frequency data.
    :param data_groupwise: DataFrame containing group-wise frequency data.
    :param median_occurrence: Median of occurrence-wise frequency.
    :param median_groupwise: Median of group-wise frequency.
    """

    for i, text in enumerate(texts):
        label = text.get_text()  # Get the current label text
        occurrence_value = data_occurrence.loc[i, 'RTC (%)']
        groupwise_value = data_groupwise.loc[i, 'RMC (%)']

        # Reset the label by removing any previous chars if necessary
        clean_label = label.split()[0]  # Get the original label without any appended chars

        # Append characters based on the conditions
        if occurrence_value >= median_occurrence and groupwise_value >= median_groupwise:
            label = f'{clean_label} +*'  # Both conditions met
        elif occurrence_value >= median_occurrence:
            label = f'{clean_label} +'  # Only occurrence-wise above the median
        elif groupwise_value >= median_groupwise:
            label = f'{clean_label} *'  # Only group-wise above the median
        else:
            label = clean_label  # Neither condition met, keep the original label

        text.set_text(label)  # Update the label
        text.set_color('black')  # Ensure the color remains black

    return texts


def save_to_csv(data, filepath, message):
    """
    Utility function to save a DataFrame to a CSV file with error handling.
    """
    try:
        df = pd.DataFrame(data)
        df.to_csv(filepath, index=False)
        logger.success(message)
    except Exception as e:
        logger.error(f"Failed to save {filepath}: {e}")


def append_unique_preserving_order(existing_list, new_keys):
    """Append keys to the list, preserving the original order and ensuring no duplicates."""
    for key in new_keys:
        if key not in existing_list:
            existing_list.append(key)
    return existing_list


def save_object(object_to_save: object, output_dir: str, output_file_name: str,
                output_description: Optional[str] = None):
    """Save an object to a compressed file using gzip and pickle."""
    try:
        # Ensure the output directory exists
        os.makedirs(output_dir, exist_ok=True)

        # Construct the full output file path
        output_file_path = os.path.join(output_dir, f"{output_file_name}.object.gz")

        # Save the object using gzip and pickle
        with gzip.open(output_file_path, "wb") as file:
            pickle.dump(object_to_save, file)

        # Log success message
        if output_description:
            logger.success(f"{output_description} successfully saved as {output_file_path}.")
        else:
            logger.success(f"Object successfully saved as {output_file_path}.")

    except (OSError, pickle.PickleError) as e:
        logger.error(f"Failed to save the object. Error: {e}")
    except Exception as e:
        # Catch any other exceptions and log them
        logger.error(f"An unexpected error occurred: {e}")


def create_visualizations_out_dirs(output_dir, dataset_name):
    # Base directory
    output_dir = os.path.join(output_dir, dataset_name)

    # Subdirectories
    subdirs = ["class_clean", "relation_clean"]
    paths = [os.path.join(output_dir, subdir) for subdir in subdirs]

    # Create directories if they don't exist
    for path in paths:
        os.makedirs(path, exist_ok=True)

    # Unpack and return the paths
    return tuple(paths)


def load_object(input_source: Union[object, str], description: Optional[str] = None) -> object:
    """
    Loads an object from a given source. If the input source is a string, it is assumed to be a file path to
    a serialized (pickled and gzipped) object, which will be deserialized. If the input is already an object,
    it is returned as-is.
    """
    if isinstance(input_source, str):
        # Deserialize (unpickle) the object from the provided file path
        description = description or "object"
        logger.info(f"Loading {description} from {input_source}.")

        try:
            with gzip.open(input_source, "rb") as file:
                input_source = pickle.load(file)
            logger.success(f"Successfully loaded {description}.")
        except (FileNotFoundError, OSError, pickle.PickleError) as e:
            logger.error(f"Failed to load {description} from {input_source}: {e}")
            raise

    return input_source
