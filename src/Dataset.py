import csv
import math
import os

import numpy as np
import pandas as pd
from loguru import logger

from src import ModelData
from src.calculations.statistics_calculations_datasets import calculate_class_and_relation_metrics, calculate_stats, \
    calculate_ratios
from src.calculations.statistics_calculations_stereotypes import calculate_stereotype_metrics
from src.utils import append_unique_preserving_order, save_to_csv


class Dataset():
    def __init__(self, name: str, models: list[ModelData]) -> None:

        self.name: str = name
        self.models: list[ModelData] = models

        self.num_classes: int = -1
        self.num_relations: int = -1

        self.statistics = {}
        self.statistics_invalids = {}

        self.years_stereotypes_data = {}

        self.class_statistics_raw = {}
        self.class_statistics_clean = {}

        self.relation_statistics_raw = {}
        self.relation_statistics_clean = {}

        self.combined_statistics_raw = {}
        self.combined_statistics_clean = {}

    def save_dataset_general_data_csv(self, output_dir: str) -> None:
        output_dir = os.path.join(output_dir, self.name)

        # Create folder if it does not exist
        os.makedirs(output_dir, exist_ok=True)

        # Prepare the data for the CSV
        data = [[model.name, model.year, model.total_class_number, model.total_relation_number] for model in
                self.models]
        df = pd.DataFrame(data, columns=["model", "year", "total_class_number", "total_relation_number"])

        # Save to CSV using the common utility function
        filepath = os.path.join(output_dir, f'{self.name}_basic_data.csv')
        save_to_csv(df, filepath, f"General data for dataset '{self.name}' successfully saved to {filepath}.")

    def save_dataset_class_data_csv(self, output_dir: str) -> None:
        output_dir = os.path.join(output_dir, self.name)

        # Create folder if it does not exist
        os.makedirs(output_dir, exist_ok=True)

        # Extract all the stereotypes from the first model
        stereotypes = list(self.models[0].class_stereotypes.keys())

        # Create a DataFrame for class data
        data = [[model.name] + [model.class_stereotypes[st] for st in stereotypes] for model in self.models]
        df = pd.DataFrame(data, columns=["model"] + stereotypes)
        self.data_class = df

        # Save to CSV using the common utility function
        filepath = os.path.join(output_dir, f'{self.name}_class_data.csv')
        save_to_csv(df, filepath, f"Class data for dataset '{self.name}' successfully saved to {filepath}.")

    def save_dataset_relation_data_csv(self, output_dir: str) -> None:
        output_dir = os.path.join(output_dir, self.name)

        # Create folder if it does not exist
        os.makedirs(output_dir, exist_ok=True)

        # Extract all the relation stereotypes from the first model
        stereotypes = list(self.models[0].relation_stereotypes.keys())

        # Create a DataFrame for relation data
        data = [[model.name] + [model.relation_stereotypes[st] for st in stereotypes] for model in self.models]
        df = pd.DataFrame(data, columns=["model"] + stereotypes)
        self.data_relation = df

        # Save to CSV using the common utility function
        filepath = os.path.join(output_dir, f'{self.name}_relation_data.csv')
        save_to_csv(df, filepath, f"Relation data for dataset '{self.name}' successfully saved to {filepath}.")

    def calculate_dataset_statistics(self) -> None:
        """Calculates statistics and metrics for the dataset and stores them in self.statistics."""

        # Step 1: Prepare the data for class and relation metrics
        class_data = self._create_dataframe_for_stereotypes("class_stereotypes")
        relation_data = self._create_dataframe_for_stereotypes("relation_stereotypes")

        # Step 2: Calculate class and relation metrics
        class_metrics, class_total, class_stereotyped, class_non_stereotyped, class_ontouml, class_non_ontouml = calculate_class_and_relation_metrics(
            class_data, 'classes')
        relation_metrics, relation_total, relation_stereotyped, relation_non_stereotyped, relation_ontouml, relation_non_ontouml = calculate_class_and_relation_metrics(
            relation_data, 'relations')

        # Step 3: Calculate statistics for the dataset
        metrics = {'class_total': calculate_stats(class_total), 'class_stereotyped': calculate_stats(class_stereotyped),
                   'class_non_stereotyped': calculate_stats(class_non_stereotyped),
                   'class_ontouml': calculate_stats(class_ontouml),
                   'class_non_ontouml': calculate_stats(class_non_ontouml),
                   'relation_total': calculate_stats(relation_total),
                   'relation_stereotyped': calculate_stats(relation_stereotyped),
                   'relation_non_stereotyped': calculate_stats(relation_non_stereotyped),
                   'relation_ontouml': calculate_stats(relation_ontouml),
                   'relation_non_ontouml': calculate_stats(relation_non_ontouml)}

        # Step 4: Calculate ratios
        ratios = calculate_ratios(class_metrics['total_classes'], relation_metrics['total_relations'],
                                  class_metrics['stereotyped_classes'], relation_metrics['stereotyped_relations'],
                                  class_metrics['non_stereotyped_classes'],
                                  relation_metrics['non_stereotyped_relations'], class_metrics['ontouml_classes'],
                                  relation_metrics['ontouml_relations'], class_metrics['non_ontouml_classes'],
                                  relation_metrics['non_ontouml_relations'])

        # Step 5: Store the results in the statistics dictionary
        self.statistics.update(class_metrics)
        self.statistics.update(relation_metrics)
        self.statistics.update(ratios)

        # Step 6: Store all calculated statistics in self.statistics
        for key, stat_dict in metrics.items():
            for stat_name, value in stat_dict.items():
                self.statistics[f'{key}_{stat_name}'] = value

        self.num_classes = self.statistics["total_classes"]
        self.num_relations = self.statistics["total_relations"]
        assert self.num_classes != -1  # value attributed
        assert self.num_relations != -1  # value attributed

        logger.success(f"Statistics calculated for dataset '{self.name}'.")

    def _create_dataframe_for_stereotypes(self, stereotype_type: str) -> pd.DataFrame:
        """Helper function to create a DataFrame from class or relation stereotypes."""
        if stereotype_type not in ['class_stereotypes', 'relation_stereotypes']:
            raise ValueError("Invalid stereotype_type. Must be 'class_stereotypes' or 'relation_stereotypes'.")

        data = []
        for model in self.models:
            if stereotype_type == "class_stereotypes":
                data.append(model.class_stereotypes)
            else:
                data.append(model.relation_stereotypes)

        df = pd.DataFrame(data)
        df.insert(0, 'model', [model.name for model in self.models])  # Insert model names as the first column
        return df

    def calculate_models_statistics(self) -> None:
        """
        Calculate the statistics for all models in the dataset.
        """

        # Ensure statistics are calculated for each model
        for model in self.models:
            model.calculate_statistics()

    def save_models_statistics_to_csv(self, output_csv_dir: str) -> None:
        """
        Save statistics from a list of models to a CSV file dynamically.
        """
        # Use a list to preserve insertion order and avoid duplicates
        all_keys = []

        # Collect all the unique statistics keys from the models in this dataset
        for model in self.models:
            # Add logging to check if model.statistics exists and is a dictionary
            if isinstance(model.statistics, dict):
                all_keys = append_unique_preserving_order(all_keys, model.statistics.keys())
            else:
                logger.error(f"Model '{model.name}' does not have a valid statistics dictionary.")

        # Define the output directory
        output_dir = os.path.join(output_csv_dir, self.name)

        # Create the folder if it does not exist
        os.makedirs(output_dir, exist_ok=True)

        output_path = os.path.join(output_dir, f"{self.name}_models_statistics.csv")

        # Open the CSV file for writing
        with open(output_path, mode='w', newline='') as file:
            writer = csv.writer(file)

            # Write the header (model, dynamic keys)
            writer.writerow(['model'] + all_keys)

            # Write the statistics for each model
            for model in self.models:
                row = [model.name]  # Start the row with the model name

                # Check for each key, retrieve the value, handle NaN if applicable
                for key in all_keys:
                    value = model.statistics.get(key, 'N/A')  # Get the value or default to 'N/A'

                    # Check if the value is a number and if it's NaN
                    if isinstance(value, (int, float)) and math.isnan(value):
                        row.append('N/A')
                    else:
                        row.append(value)

                # Write the row to the CSV file
                writer.writerow(row)

        logger.success(f"Statistics for models in dataset '{self.name}' successfully saved in {output_path}.")

    def calculate_stereotype_statistics(self) -> None:
        """
        Calculate stereotype statistics for class and relation stereotypes, both raw and clean,
        and store the results in the corresponding dictionaries.
        """
        # Step 1: Calculate raw statistics (without cleaning 'none' and 'other') for class and relation stereotypes
        self.class_statistics_raw = calculate_stereotype_metrics(self.models, 'class', filter_type=False)
        self.relation_statistics_raw = calculate_stereotype_metrics(self.models, 'relation', filter_type=False)
        self.combined_statistics_raw = calculate_stereotype_metrics(self.models, 'combined', filter_type=False)

        # Step 2: Calculate clean statistics (with filtering 'none' and 'other') for class and relation stereotypes
        self.class_statistics_clean = calculate_stereotype_metrics(self.models, 'class', filter_type=True)
        self.relation_statistics_clean = calculate_stereotype_metrics(self.models, 'relation', filter_type=True)
        self.combined_statistics_clean = calculate_stereotype_metrics(self.models, 'combined', filter_type=True)

        logger.success(f"Stereotype statistics calculated for dataset '{self.name}'.")

    def save_stereotype_statistics(self, output_dir: str) -> None:
        """
        Save all stereotype statistics (class/relation, raw/clean) to separate CSV files in different folders.
        :param output_dir: Directory where the CSV files will be saved.
        """
        # Define subdirectories for class/relation and raw/clean data
        subdirs = {'class_raw': self.class_statistics_raw, 'relation_raw': self.relation_statistics_raw,
                   'class_clean': self.class_statistics_clean, 'relation_clean': self.relation_statistics_clean,
                   'combined_raw': self.combined_statistics_raw, 'combined_clean': self.combined_statistics_clean}

        # Create the output directories and save the statistics
        for subdir, statistics in subdirs.items():
            # Create the specific folder (e.g., class_raw, relation_raw, etc.)
            output_subdir = os.path.join(output_dir, self.name, subdir)

            os.makedirs(output_subdir, exist_ok=True)

            # Save the statistics to CSV files
            for stat_name, dataframe in statistics.items():
                stat_name_cleaned = stat_name.lower().replace(" ", "_")
                filepath = os.path.join(output_subdir, f"{stat_name_cleaned}.csv")
                save_to_csv(dataframe, filepath,
                            f"Dataset {self.name}, case '{subdir}', statistic '{stat_name}' saved successfully in '{filepath}'.")

    def calculate_and_save_stereotypes_by_year(self, output_dir: str) -> pd.DataFrame:
        # Create dictionaries to hold the sum of stereotypes per year for class and relation (occurrence-wise and model-wise)
        yearly_data_class_ow = {}
        yearly_data_relation_ow = {}
        yearly_data_class_mw = {}
        yearly_data_relation_mw = {}

        cases = {'class': (self.data_class, yearly_data_class_ow, yearly_data_class_mw),
                 'relation': (self.data_relation, yearly_data_relation_ow, yearly_data_relation_mw)}

        # Loop through each model and accumulate the stereotype counts by year
        for analysis, (content, yearly_data_ow, yearly_data_mw) in cases.items():
            for model in self.models:
                model_year = model.year

                if model_year not in yearly_data_ow:
                    yearly_data_ow[model_year] = np.zeros(len(content.columns) - 1,
                                                          dtype=int)  # Initialize with zeros for occurrence-wise calculation
                if model_year not in yearly_data_mw:
                    yearly_data_mw[model_year] = np.zeros(len(content.columns) - 1,
                                                          dtype=int)  # Initialize with zeros for model-wise calculation

                # Fetch the row for the current model and ensure it matches the expected length
                model_data = content.loc[content['model'] == model.name].iloc[0, 1:].astype(int).values

                if len(model_data) == len(yearly_data_ow[model_year]):
                    # Occurrence-wise: Sum the stereotype counts for each year
                    yearly_data_ow[model_year] += model_data

                    # Model-wise: Check where a stereotype occurs (binary approach)
                    yearly_data_mw[model_year] += (model_data > 0).astype(int)
                else:
                    raise ValueError(f"Mismatch in number of columns for model {model.name} in {analysis} analysis.")

            # Convert the dictionaries to DataFrames (both occurrence-wise and model-wise)
            stereotypes = content.columns[1:]  # Get the stereotype names
            df_yearly_ow = pd.DataFrame.from_dict(yearly_data_ow, orient='index', columns=stereotypes)
            df_yearly_mw = pd.DataFrame.from_dict(yearly_data_mw, orient='index', columns=stereotypes)

            # Set the 'year' as the index
            df_yearly_ow.index.name = 'year'
            df_yearly_mw.index.name = 'year'

            # Sort the DataFrames by the 'year' index in ascending order
            df_yearly_ow = df_yearly_ow.sort_index(ascending=True)
            df_yearly_mw = df_yearly_mw.sort_index(ascending=True)

            # Store the occurrence-wise and model-wise results in years_stereotypes_data
            self.years_stereotypes_data[f'{analysis}_ow'] = df_yearly_ow
            self.years_stereotypes_data[f'{analysis}_mw'] = df_yearly_mw

            # Normalize both occurrence-wise and model-wise results
            self._normalize_stereotypes_overall(f'{analysis}_ow')
            self._normalize_stereotypes_yearly(f'{analysis}_ow')
            self._normalize_stereotypes_overall(f'{analysis}_mw')
            self._normalize_stereotypes_yearly(f'{analysis}_mw')

        # Define the keys for saving the data
        keys = ['class_ow', 'relation_ow', 'class_mw', 'relation_mw', 'class_ow_overall', 'relation_ow_overall',
                'class_ow_yearly', 'relation_ow_yearly', 'class_mw_overall', 'relation_mw_overall', 'class_mw_yearly',
                'relation_mw_yearly']

        # Save each of the DataFrames to CSV files
        for key in keys:
            # Create the correct folder structure for class and relation
            if 'class' in key:
                output_dir_final = os.path.join(output_dir, self.name, "class_raw")
            elif 'relation' in key:
                output_dir_final = os.path.join(output_dir, self.name, "relation_raw")
            else:
                raise ValueError("Unexpected key in years_stereotypes_data.")

            # Create the directory if it does not exist
            os.makedirs(output_dir_final, exist_ok=True)

            # Save the DataFrame to a CSV file
            csv_path = os.path.join(output_dir_final, f'years_stereotypes_{key}.csv')
            self.years_stereotypes_data[key].to_csv(csv_path)
            logger.success(f"{key} stereotypes data saved to {csv_path}.")

    def calculate_and_save_models_by_year(self, output_dir: str):
        # Initialize dictionaries to count the number of models per year
        model_count = {}

        # Loop through self.models to count models for each year based on whether they have class or relation data
        for model in self.models:
            model_year = model.year

            if model_year not in model_count:
                model_count[model_year] = 0
            model_count[model_year] += 1  # Assuming all models have at least one stereotype of any type

        # Convert the dictionaries into DataFrames
        df_model_count = pd.DataFrame(list(model_count.items()), columns=['year', 'num_models'])

        # Calculate the total number of models
        total_models = df_model_count['num_models'].sum()

        # Calculate the ratio
        df_model_count['ratio'] = df_model_count['num_models'] / total_models

        # Sort by year to ensure chronological order
        df_model_count = df_model_count.sort_values(by='year').reset_index(drop=True)

        # Store the results in self.years_models_number
        self.years_models_number = df_model_count

        # Create folder if it does not exist
        output_dir_final = os.path.join(output_dir, self.name)
        os.makedirs(output_dir_final, exist_ok=True)

        # Save models per year data
        models_csv_path = os.path.join(output_dir_final, 'years_models_number.csv')
        self.years_models_number.to_csv(models_csv_path, index=False)
        logger.success(f"Models per year data saved to {models_csv_path}.")

    def _normalize_stereotypes_overall(self, case) -> None:
        df = self.years_stereotypes_data[case]

        # Sum of all values in the DataFrame (excluding the 'year' index)
        total_sum = df.to_numpy().sum()

        # Normalize the DataFrame so that the sum of all values is 1
        df_normalized = df / total_sum

        # Store the result in years_stereotypes_data for overall normalization
        self.years_stereotypes_data[f'{case}_overall'] = df_normalized

    def _normalize_stereotypes_yearly(self, case) -> None:
        # Normalize for both 'class' and 'relation'
        df = self.years_stereotypes_data[case]

        # Normalize each row so that the sum of values in each row is 1
        df_normalized = df.div(df.sum(axis=1), axis=0)

        # Store the result in years_stereotypes_data for yearly normalization
        self.years_stereotypes_data[f'{case}_yearly'] = df_normalized

    def save_stereotypes_count_by_year(self, output_dir: str) -> None:
        """
        Save a CSV file that reports the number of class and relation stereotypes for each year, including ratio, cumulative,
        ontouml, none, and other class/relation columns, and their respective ratios and cumulative values.
        """
        # Initialize a dictionary to hold the stereotype counts per year
        year_data = {}

        # Loop through each model and accumulate class and relation stereotypes by year
        for model in self.models:
            model_year = model.year

            # Initialize the year entry if not present
            if model_year not in year_data:
                year_data[model_year] = {'num_class': 0, 'ontouml_class': 0, 'none_class': 0, 'other_class': 0,
                                         'num_relation': 0, 'ontouml_relation': 0, 'none_relation': 0,
                                         'other_relation': 0}

            # Process class stereotypes
            for stereotype, count in model.class_stereotypes.items():
                year_data[model_year]['num_class'] += count
                if stereotype == 'none':
                    year_data[model_year]['none_class'] += count
                elif stereotype == 'other':
                    year_data[model_year]['other_class'] += count
                else:
                    year_data[model_year]['ontouml_class'] += count

            # Process relation stereotypes
            for stereotype, count in model.relation_stereotypes.items():
                year_data[model_year]['num_relation'] += count
                if stereotype == 'none':
                    year_data[model_year]['none_relation'] += count
                elif stereotype == 'other':
                    year_data[model_year]['other_relation'] += count
                else:
                    year_data[model_year]['ontouml_relation'] += count

        # Convert the dictionary to a DataFrame for easier CSV saving
        df_year_data = pd.DataFrame.from_dict(year_data, orient='index').reset_index()
        df_year_data.columns = ['year', 'num_class', 'ontouml_class', 'none_class', 'other_class', 'num_relation',
                                'ontouml_relation', 'none_relation', 'other_relation']

        # Sort by year to ensure chronological order
        df_year_data = df_year_data.sort_values(by='year').reset_index(drop=True)

        # Calculate the totals for classes and relations
        total_classes = df_year_data['num_class'].sum()
        total_relations = df_year_data['num_relation'].sum()

        total_ontouml_classes = df_year_data['ontouml_class'].sum()
        total_none_classes = df_year_data['none_class'].sum()
        total_other_classes = df_year_data['other_class'].sum()

        total_ontouml_relations = df_year_data['ontouml_relation'].sum()
        total_none_relations = df_year_data['none_relation'].sum()
        total_other_relations = df_year_data['other_relation'].sum()

        # Ratio and cumulative columns for classes
        df_year_data['ratio_class'] = df_year_data['num_class'] / total_classes
        df_year_data['cumulative_class'] = df_year_data['num_class'].cumsum()
        df_year_data['cumulative_ratio_class'] = df_year_data['cumulative_class'] / total_classes

        # Ratio and cumulative columns for ontouml, none, other classes
        df_year_data['ratio_ontouml_class'] = df_year_data['ontouml_class'] / total_ontouml_classes

        df_year_data['cumulative_ontouml_class'] = df_year_data['ontouml_class'].cumsum()
        df_year_data['cumulative_ratio_ontouml_class'] = df_year_data[
                                                             'cumulative_ontouml_class'] / total_ontouml_classes

        df_year_data['ratio_none_class'] = df_year_data['none_class'] / total_none_classes
        df_year_data['cumulative_none_class'] = df_year_data['none_class'].cumsum()
        df_year_data['cumulative_ratio_none_class'] = df_year_data['cumulative_none_class'] / total_none_classes

        df_year_data['ratio_other_class'] = df_year_data['other_class'] / total_other_classes
        df_year_data['cumulative_other_class'] = df_year_data['other_class'].cumsum()
        df_year_data['cumulative_ratio_other_class'] = df_year_data['cumulative_other_class'] / total_other_classes

        # Ratio and cumulative columns for relations
        df_year_data['ratio_relation'] = df_year_data['num_relation'] / total_relations
        df_year_data['cumulative_relation'] = df_year_data['num_relation'].cumsum()
        df_year_data['cumulative_ratio_relation'] = df_year_data['cumulative_relation'] / total_relations

        # Ratio and cumulative columns for ontouml, none, other relations
        df_year_data['ratio_ontouml_relation'] = df_year_data['ontouml_relation'] / total_ontouml_relations
        df_year_data['cumulative_ontouml_relation'] = df_year_data['ontouml_relation'].cumsum()
        df_year_data['cumulative_ratio_ontouml_relation'] = df_year_data[
                                                                'cumulative_ontouml_relation'] / total_ontouml_relations

        df_year_data['ratio_none_relation'] = df_year_data['none_relation'] / total_none_relations
        df_year_data['cumulative_none_relation'] = df_year_data['none_relation'].cumsum()
        df_year_data['cumulative_ratio_none_relation'] = df_year_data['cumulative_none_relation'] / total_none_relations

        df_year_data['ratio_other_relation'] = df_year_data['other_relation'] / total_other_relations
        df_year_data['cumulative_other_relation'] = df_year_data['other_relation'].cumsum()
        df_year_data['cumulative_ratio_other_relation'] = df_year_data[
                                                              'cumulative_other_relation'] / total_other_relations

        # Ratios related to general category

        df_year_data['ratio_ontouml_to_total_class'] = df_year_data['ontouml_class'] / total_classes
        df_year_data['ratio_none_to_total_class'] = df_year_data['none_class'] / total_classes
        df_year_data['ratio_other_to_total_class'] = df_year_data['other_class'] / total_classes

        df_year_data['ratio_ontouml_to_total_relation'] = df_year_data['ontouml_relation'] / total_relations
        df_year_data['ratio_none_to_total_relation'] = df_year_data['none_relation'] / total_relations
        df_year_data['ratio_other_to_total_relation'] = df_year_data['other_relation'] / total_relations

        df_year_data['cumulative_ratio_ontouml_to_total_class'] = df_year_data[
                                                                      'cumulative_ontouml_class'] / total_classes
        df_year_data['cumulative_ratio_none_to_total_class'] = df_year_data['cumulative_none_class'] / total_classes
        df_year_data['cumulative_ratio_other_to_total_class'] = df_year_data['cumulative_other_class'] / total_classes

        df_year_data['cumulative_ratio_ontouml_to_total_relation'] = df_year_data[
                                                                         'cumulative_ontouml_relation'] / total_relations
        df_year_data['cumulative_ratio_none_to_total_relation'] = df_year_data[
                                                                      'cumulative_none_relation'] / total_relations
        df_year_data['cumulative_ratio_other_to_total_relation'] = df_year_data[
                                                                       'cumulative_other_relation'] / total_relations

        # Define output directory and create it if necessary
        output_dir_final = os.path.join(output_dir, self.name)
        os.makedirs(output_dir_final, exist_ok=True)

        # Save the DataFrame to a CSV file
        csv_path = os.path.join(output_dir_final, 'stereotypes_count_by_year.csv')
        df_year_data.to_csv(csv_path, index=False)

        logger.success(f"Stereotypes count by year data saved to {csv_path}.")

    def calculate_invalid_stereotypes_metrics(self) -> None:
        """
        Calculate metrics for invalid stereotypes across all models in the dataset
        and store them in self.statistics_invalids as separate dictionaries for
        class and relation invalid stereotypes.
        """
        # Initialize dictionaries to track metrics for class and relation stereotypes
        invalid_class_metrics = {}
        invalid_relation_metrics = {}

        # Iterate over all models in the dataset
        for model in self.models:
            # Collect invalid class stereotypes
            for stereotype, count in model.invalid_class_stereotypes.items():
                if stereotype not in invalid_class_metrics:
                    invalid_class_metrics[stereotype] = {'accumulated_frequency': 0, 'model_coverage': 0}
                invalid_class_metrics[stereotype]['accumulated_frequency'] += count
                invalid_class_metrics[stereotype]['model_coverage'] += 1  # Each model contributes once per stereotype

            # Collect invalid relation stereotypes
            for stereotype, count in model.invalid_relation_stereotypes.items():
                if stereotype not in invalid_relation_metrics:
                    invalid_relation_metrics[stereotype] = {'accumulated_frequency': 0, 'model_coverage': 0}
                invalid_relation_metrics[stereotype]['accumulated_frequency'] += count
                invalid_relation_metrics[stereotype][
                    'model_coverage'] += 1  # Each model contributes once per stereotype

        # Store results in self.statistics_invalids
        self.statistics_invalids = {'class': invalid_class_metrics, 'relation': invalid_relation_metrics}

    def save_invalid_stereotypes_metrics_to_csv(self, output_dir: str) -> None:
        """
        Save the calculated invalid stereotypes metrics to two separate CSV files:
        - One for invalid class stereotypes
        - One for invalid relation stereotypes

        Args:
            output_dir (str): Directory where the CSV files will be saved.
        """
        # Ensure the metrics are calculated
        if not self.statistics_invalids:
            logger.warning(
                "Invalid stereotypes metrics have not been calculated. Call calculate_invalid_stereotypes_metrics() first.")
            return

        # Extract class and relation invalid metrics
        invalid_class_metrics = self.statistics_invalids.get('class', {})
        invalid_relation_metrics = self.statistics_invalids.get('relation', {})

        # Prepare output directory
        output_dir = os.path.join(output_dir, self.name)
        os.makedirs(output_dir, exist_ok=True)

        # Save class invalid stereotypes
        if invalid_class_metrics:
            class_data = [{'stereotype': stereotype, 'accumulated_frequency': metrics['accumulated_frequency'],
                           'model_coverage': metrics['model_coverage']} for stereotype, metrics in
                          invalid_class_metrics.items()]
            class_filepath = os.path.join(output_dir, f"{self.name}_invalid_class_stereotypes_metrics.csv")
            class_df = pd.DataFrame(class_data)
            class_df.to_csv(class_filepath, index=False, sep=';', header=True)
            logger.success(f"Invalid class stereotypes metrics saved successfully to {class_filepath}.")
        else:
            logger.info(f"No invalid class stereotypes found for dataset '{self.name}'.")

        # Save relation invalid stereotypes
        if invalid_relation_metrics:
            relation_data = [{'stereotype': stereotype, 'accumulated_frequency': metrics['accumulated_frequency'],
                              'model_coverage': metrics['model_coverage']} for stereotype, metrics in
                             invalid_relation_metrics.items()]
            relation_filepath = os.path.join(output_dir, f"{self.name}_invalid_relation_stereotypes_metrics.csv")
            relation_df = pd.DataFrame(relation_data)
            relation_df.to_csv(relation_filepath, index=False, sep=';', header=True)
            logger.success(f"Invalid relation stereotypes metrics saved successfully to {relation_filepath}.")
        else:
            logger.info(f"No invalid relation stereotypes found for dataset '{self.name}'.")

    def calculate_analysis2(self):
        """
        Calculate AF (Aggregate Frequency), MC (Model Coverage), and their ratios for specific groups of stereotypes,
        and store the results in the analysis2 attribute. Includes "all" metrics for OntoUML, None, and Other.
        """

        # Initialize the analysis2 dictionary
        self.analysis2 = {
            "class": {},
            "relation": {}
        }

        # Define groups and their conditions
        def group_conditions(ontouml_count, none_count, other_count):
            return {
                "ontouml_and_other_and_none": ontouml_count > 0 and other_count > 0 and none_count > 0,
                "ontouml_and_other_and_not_none": ontouml_count > 0 and other_count > 0 and none_count == 0,
                "ontouml_and_not_other_and_none": ontouml_count > 0 and other_count == 0 and none_count > 0,
                "ontouml_and_not_other_and_not_none": ontouml_count > 0 and other_count == 0 and none_count == 0,
                "not_ontouml_and_other_and_none": ontouml_count == 0 and other_count > 0 and none_count > 0,
                "not_ontouml_and_other_and_not_none": ontouml_count == 0 and other_count > 0 and none_count == 0,
                "not_ontouml_and_not_other_and_none": ontouml_count == 0 and other_count == 0 and none_count > 0,
                "not_ontouml_and_not_other_and_not_none": ontouml_count == 0 and other_count == 0 and none_count == 0,
            }

        # Helper function to calculate AF, MC, their ratios, and all metrics
        def calculate_metrics(models, stereotype_type):
            # Initialize metrics dictionary
            metrics = {
                "af": {key: 0 for key in group_conditions(0, 0, 0)},
                "mc": {key: 0 for key in group_conditions(0, 0, 0)},
                "ratio_af": {},
                "ratio_mc": {},
                "all": {"ontouml": 0, "none": 0, "other": 0},  # Aggregated metrics
            }

            # Total counts for ratios
            total_stereotypes = sum(
                sum(value for key, value in model.class_stereotypes.items())
                if stereotype_type == "class"
                else sum(value for key, value in model.relation_stereotypes.items())
                for model in models
            )
            if stereotype_type == "relation":
                models_with_relations = [model for model in models if sum(model.relation_stereotypes.values()) > 0]
                total_models = len(models_with_relations)
            else:
                total_models = len(models)

            # Iterate over models to calculate AF and MC
            # Inside calculate_metrics
            for model in models:
                # Extract the stereotype dictionary based on the stereotype type
                stereotypes = (
                    model.class_stereotypes if stereotype_type == "class" else model.relation_stereotypes
                )

                # Calculate the total number of stereotypes for this model
                total_count = sum(stereotypes.values())

                # Skip processing if there are no stereotypes
                if total_count == 0:
                    continue

                # Aggregate counts for groups
                ontouml_count = sum(value for key, value in stereotypes.items() if key not in ["none", "other"])
                none_count = stereotypes["none"]
                other_count = stereotypes["other"]

                # Apply group conditions and update metrics
                for condition, check in group_conditions(ontouml_count, none_count, other_count).items():
                    if check:
                        metrics["af"][condition] += ontouml_count + none_count + other_count
                        metrics["mc"][condition] += 1

                # Update "all" metrics
                metrics["all"]["ontouml"] += ontouml_count
                metrics["all"]["none"] += none_count
                metrics["all"]["other"] += other_count

            # Generate ratio keys for group conditions
            for condition in metrics["af"]:
                af_value = metrics["af"][condition]
                mc_value = metrics["mc"][condition]

                metrics["ratio_af"][condition] = af_value / total_stereotypes if total_stereotypes > 0 else 0
                metrics["ratio_mc"][condition] = mc_value / total_models if total_models > 0 else 0

            # Add "all" metrics (AF and MC)
            metrics["af"]["all_ontouml"] = metrics["all"]["ontouml"]
            metrics["af"]["all_none"] = metrics["all"]["none"]
            metrics["af"]["all_other"] = metrics["all"]["other"]

            metrics["mc"]["all_ontouml"] = sum(1 for model in models if sum(
                value for key, value in
                (model.class_stereotypes if stereotype_type == "class" else model.relation_stereotypes).items()
                if key not in ["none", "other"]
            ) > 0)
            metrics["mc"]["all_none"] = sum(1 for model in models if (
                model.class_stereotypes if stereotype_type == "class" else model.relation_stereotypes)["none"] > 0)
            metrics["mc"]["all_other"] = sum(1 for model in models if (
                model.class_stereotypes if stereotype_type == "class" else model.relation_stereotypes)["other"] > 0)

            # Generate "all" ratios
            metrics["ratio_af"]["all_ontouml"] = metrics["all"][
                                                     "ontouml"] / total_stereotypes if total_stereotypes > 0 else 0
            metrics["ratio_af"]["all_none"] = metrics["all"]["none"] / total_stereotypes if total_stereotypes > 0 else 0
            metrics["ratio_af"]["all_other"] = metrics["all"][
                                                   "other"] / total_stereotypes if total_stereotypes > 0 else 0

            metrics["ratio_mc"]["all_ontouml"] = metrics["mc"]["all_ontouml"] / total_models if total_models > 0 else 0
            metrics["ratio_mc"]["all_none"] = metrics["mc"]["all_none"] / total_models if total_models > 0 else 0
            metrics["ratio_mc"]["all_other"] = metrics["mc"]["all_other"] / total_models if total_models > 0 else 0

            # Remove the "all" key to avoid duplicate columns
            del metrics["all"]

            return metrics

        # Calculate metrics for class and relation stereotypes
        self.analysis2["class"] = calculate_metrics(self.models, "class")
        self.analysis2["relation"] = calculate_metrics(self.models, "relation")

        # Log the results for debugging or confirmation
        logger.success("Analysis2 (AF, MC, Ratios, and All metrics) calculated and stored successfully.")

    def save_analysis2_to_csv(self, output_dir: str) -> None:
        """
        Save the `analysis2` results to a CSV file with two rows: one for the header and one for the values.

        - Columns: {type}_{metric}, where type = class | relation, and metric = af | mc | ratio_af | ratio_mc
        - Rows: All eight combinations of (ontouml | other | none) and (true | false), plus all_(ontouml | none | other).
        """

        # Ensure the output directory exists
        os.makedirs(output_dir, exist_ok=True)

        # Prepare the output file path
        file_path = os.path.join(output_dir, f'{self.name}_analysis2.csv')

        # Define rows (all combinations and "all" metrics)
        rows = ["ontouml_and_other_and_none", "ontouml_and_other_and_not_none", "ontouml_and_not_other_and_none",
                "ontouml_and_not_other_and_not_none", "not_ontouml_and_other_and_none",
                "not_ontouml_and_other_and_not_none", "not_ontouml_and_not_other_and_none",
                "not_ontouml_and_not_other_and_not_none", "all_ontouml", "all_none", "all_other", ]

        # Define columns (class and relation with all metrics)
        columns = []
        for stereotype_type in ["class", "relation"]:
            for metric in ["af", "mc", "ratio_af", "ratio_mc"]:
                columns.append(f"{stereotype_type}_{metric}")

        # Initialize a dictionary to hold the row values for each combination
        results = {row: [] for row in rows}

        # Fill in the results for each combination and each column
        for stereotype_type in ["class", "relation"]:
            metrics = self.analysis2[stereotype_type]

            for metric in ["af", "mc", "ratio_af", "ratio_mc"]:
                for row in rows:
                    # Get the value for the specific combination and metric
                    value = metrics[metric].get(row, "N/A")  # Use "N/A" if the value is missing
                    results[row].append(value)

        # Write the results to a CSV file
        with open(file_path, mode="w", newline="") as file:
            writer = csv.writer(file)

            # Write the header (columns)
            writer.writerow(["combination"] + columns)

            # Write the rows
            for row, values in results.items():
                writer.writerow([row] + values)

        # Log success message
        logger.success(f"Analysis2 results saved in alternate format successfully to {file_path}.")

    def general_validation(self) -> None:
        """
        Perform general validations to ensure the integrity of the dataset calculations.
        Validates:
        - Consistency of class and relation ratios.
        - Consistency of AF, MC, and ratio calculations in analysis2.
        """

        # Validate AF and MC for both class and relation stereotypes
        for stereotype_type in ["class", "relation"]:
            metrics = self.analysis2[stereotype_type]

            # Calculate expected total AF and MC dynamically
            expected_af = sum(
                model.total_class_number if stereotype_type == "class" else model.total_relation_number
                for model in self.models
            )
            total_af = sum(value for key, value in metrics["af"].items() if not key.startswith("all_"))
            assert math.isclose(total_af, expected_af, rel_tol=1e-5), (
                f"Total AF for {stereotype_type} does not match. Found: {total_af}, Expected: {expected_af}."
            )

            # Calculate expected total MC
            if stereotype_type == "relation":
                expected_mc = sum(1 for model in self.models if sum(model.relation_stereotypes.values()) > 0)
            else:
                expected_mc = len(self.models)
            total_mc = sum(value for key, value in metrics["mc"].items() if not key.startswith("all_"))
            assert total_mc <= expected_mc, (
                f"Total MC for {stereotype_type} exceeds the number of models. Found: {total_mc}, Expected: {expected_mc}."
            )

            # Validate ratio consistency
            for condition, af_value in metrics["af"].items():
                if condition.startswith("all_"):  # Skip aggregated keys
                    continue

                ratio_af = metrics["ratio_af"].get(condition, 0)
                assert math.isclose(ratio_af, af_value / expected_af if expected_af > 0 else 0, rel_tol=1e-5), (
                    f"AF ratio mismatch for {stereotype_type}, condition {condition}. Found: {ratio_af}, "
                    f"Expected: {af_value / expected_af if expected_af > 0 else 0}."
                )

            for condition, mc_value in metrics["mc"].items():
                if condition.startswith("all_"):  # Skip aggregated keys
                    continue

                ratio_mc = metrics["ratio_mc"].get(condition, 0)
                assert math.isclose(ratio_mc, mc_value / expected_mc if expected_mc > 0 else 0, rel_tol=1e-5), (
                    f"MC ratio mismatch for {stereotype_type}, condition {condition}. Found: {ratio_mc}, "
                    f"Expected: {mc_value / expected_mc if expected_mc > 0 else 0}."
                )

            # Validate "all_*" keys consistency
            total_all_af = metrics["af"]["all_ontouml"] + metrics["af"]["all_none"] + metrics["af"]["all_other"]
            assert math.isclose(total_af, total_all_af, rel_tol=1e-5), (
                f"Mismatch in total AF for {stereotype_type}. Found: {total_af}, Sum of all_*: {total_all_af}."
            )

            total_ratio_af = (
                    metrics["ratio_af"]["all_ontouml"]
                    + metrics["ratio_af"]["all_none"]
                    + metrics["ratio_af"]["all_other"]
            )
            assert math.isclose(total_ratio_af, 1.0, rel_tol=1e-5), (
                f"Sum of AF ratios for all_* in {stereotype_type} does not equal 1. Found: {total_ratio_af}."
            )

        logger.success("All general validations passed successfully.")
