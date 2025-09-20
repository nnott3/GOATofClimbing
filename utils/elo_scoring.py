import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging

class ELOCalculator:
    """Optimized ELO rating calculator for climbing competitions."""
    
    def __init__(self, data_dir: str = "Data/aggregate_data", k_factor: int = 32, initial_rating: int = 1500):
        self.data_dir = Path(data_dir)
        self.k_factor = k_factor
        self.initial_rating = initial_rating
        self.df = None
        self.elo_ratings = {}
        self.elo_history = []
        
        # Round priority for chronological sorting
        self.round_priority = {
            'Qualification': 0,
            'Semi-Final': 1,
            'Final': 2,
        }
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def load_data(self) -> pd.DataFrame:
        """Load and prepare competition data efficiently."""
        if not self.data_dir.exists():
            raise FileNotFoundError(f"Data directory not found: {self.data_dir}")
        
        self.logger.info("Loading competition data...")
        
        # Load all CSV files except the main aggregated one
        csv_files = [f for f in self.data_dir.glob("*.csv") if f.name != 'aggregated_results.csv']
        
        if not csv_files:
            raise ValueError("No competition data files found")
        
        # Efficient concatenation with error handling
        dfs = []
        for file in csv_files:
            try:
                df_temp = pd.read_csv(file, dtype={'round_rank': 'Int64'})  # Handle NaN ranks
                if not df_temp.empty:
                    dfs.append(df_temp)
            except Exception as e:
                self.logger.warning(f"Error loading {file}: {e}")
        
        self.df = pd.concat(dfs, ignore_index=True)
        
        # Essential cleaning only
        self.df = self.df.dropna(subset=['round_rank', 'name'])
        self.df = self.df[self.df['name'].str.strip() != '']
        self.df['name'] = self.df['name'].str.strip().str.title()

        # Optimize data types
        self.df['start_date'] = pd.to_datetime(self.df['start_date'], errors='coerce')
        self.df = self.df.dropna(subset=['start_date'])
        
        # Add sorting column
        self.df['round_order'] = self.df['round'].map(self.round_priority).fillna(99)
        
        # Critical: Sort chronologically for proper ELO calculation
        self.df = self.df.sort_values(
            ['start_date', 'event_name', 'round_order', 'round_rank'],
            kind='stable'
        ).reset_index(drop=True)
        
        self.logger.info(f"Loaded {len(self.df)} valid competition records")
        return self.df
    
    def calculate_elo_ratings(self) -> pd.DataFrame:
        """Calculate ELO ratings with proper initialization timing."""
        if self.df is None:
            self.load_data()
        
        self.logger.info("Calculating ELO ratings...")
        
        # Reset state
        self.elo_ratings.clear()
        self.elo_history.clear()
        
        # Pre-calculate first appearances for efficiency
        first_appearances = self.df.groupby('name')['start_date'].min()
        athlete_countries = self.df.groupby('name')['country'].first() if 'country' in self.df.columns else {}

        # Process competitions chronologically
        for group_key, event_data in self.df.groupby(
            ['event_name', 'start_date', 'discipline', 'gender', 'round'], 
            sort=False
        ):
            event_name, date, discipline, gender, round_type = group_key
            event_data = event_data.sort_values('round_rank')
            
            athletes = event_data['name'].tolist()
            ranks = event_data['round_rank'].tolist()
            
            # Initialize new athletes at their first appearance
            for athlete in athletes:
                if athlete not in self.elo_ratings:
                    self.elo_ratings[athlete] = self.initial_rating
                    first_date = first_appearances[athlete]
                    country = athlete_countries.get(athlete, "Unknown")
                    # Add initial rating record
                    self.elo_history.append({
                        'name': athlete,
                        'country': country,
                        'event': 'Initial Rating',
                        'year': first_date.year,
                        'date': first_date,
                        'discipline': discipline,
                        'gender': gender,
                        'round': 'Initial',
                        'rank': None,
                        'elo_before': self.initial_rating,
                        'elo_after': self.initial_rating,
                        'elo_change': 0,
                        'competed': False
                    })
            
            # Calculate ELO changes for this round
            self._process_round(athletes, ranks, event_name, date, discipline, gender, round_type, athlete_countries)
        
        # Convert to DataFrame and sort properly
        result = pd.DataFrame(self.elo_history)
        if not result.empty:
            result = result.sort_values(
                ['date', 'competed', 'name'], 
                kind='stable'
            ).reset_index(drop=True)
        
        self.logger.info(f"Calculated ELO for {len(self.elo_ratings)} athletes")
        return result
    
    def _process_round(self, athletes: List[str], ranks: List[int], 
                      event: str, date, discipline: str, gender: str, round_type: str,
                      athlete_countries: Dict[str, str] = None):
        """Process a single competition round efficiently."""
        n = len(athletes)
        if n < 2:
            return  # Skip rounds with insufficient competitors
        
        # Pre-calculate all ratings for efficiency
        ratings = [self.elo_ratings[athlete] for athlete in athletes]
        
        for i, athlete in enumerate(athletes):
            rating_before = ratings[i]
            rank_i = ranks[i]
            total_change = 0
            
            # Compare against all other athletes
            for j in range(n):
                if i != j:
                    rating_j = ratings[j]
                    rank_j = ranks[j]
                    
                    # Expected score based on rating difference
                    expected = 1 / (1 + 10 ** ((rating_j - rating_before) / 400))
                    
                    # Actual score based on ranking
                    if rank_i < rank_j:
                        actual = 1.0
                    elif rank_i > rank_j:
                        actual = 0.0
                    else:
                        actual = 0.5
                    
                    # ELO change (normalized by number of opponents)
                    total_change += self.k_factor * (actual - expected) / (n - 1)
            
            # Update rating
            self.elo_ratings[athlete] += total_change
            country = athlete_countries.get(athlete, "Unknown")
            # Record competition
            self.elo_history.append({
                'name': athlete,
                'country': country,
                'event': event,
                'year': date.year,
                'date': date,
                'discipline': discipline,
                'gender': gender,
                'round': round_type,
                'rank': rank_i,
                'elo_before': rating_before,
                'elo_after': self.elo_ratings[athlete],
                'elo_change': total_change,
                'competed': True
            })
    
    def get_current_rankings(self, discipline: str = None, gender: str = None, 
                           top_n: int = 50) -> pd.DataFrame:
        """Get current ELO rankings with optional filters."""
        if not self.elo_ratings:
            self.calculate_elo_ratings()
        
        if not self.elo_history:
            return pd.DataFrame()
        
        # Get competition history
        history_df = pd.DataFrame(self.elo_history)
        competition_df = history_df[history_df['competed'] == True]
        
        if competition_df.empty:
            return pd.DataFrame()
        
        # Apply filters
        if discipline:
            competition_df = competition_df[
                competition_df['discipline'].str.lower() == discipline.lower()
            ]
        if gender:
            competition_df = competition_df[
                competition_df['gender'].str.lower() == gender.lower()
            ]
        
        if competition_df.empty:
            return pd.DataFrame()
        
        # Get latest rating for each athlete
        latest_ratings = (
            competition_df.sort_values('date')
            .groupby('name')
            .last()[['elo_after']]
            .reset_index()
        )
        latest_ratings.rename(columns={'elo_after': 'current_elo'}, inplace=True)
        
        # # Calculate additional statistics
        # athlete_stats = competition_df.groupby('name').agg({
        #     'elo_change': ['count', 'mean'],
        #     'rank': 'mean',
        #     'elo_after': ['min', 'max']
        # }).round(2)
        
        # # Flatten column names
        # athlete_stats.columns = ['_'.join(col) for col in athlete_stats.columns]
        # athlete_stats.reset_index(inplace=True)
        # athlete_stats.rename(columns={
        #     'elo_change_count': 'competitions',
        #     'elo_change_mean': 'avg_elo_change',
        #     'rank_mean': 'avg_rank',
        #     'elo_after_min': 'min_elo',
        #     'elo_after_max': 'peak_elo'
        # }, inplace=True)
        
        # Merge and sort
        # result = latest_ratings.merge(athlete_stats, on='name', how='left')
        # result = result.sort_values('current_elo', ascending=False).head(top_n)
        
        result = latest_ratings.sort_values('current_elo', ascending=False).head(top_n)
        
        return result.reset_index(drop=True)
    
    def get_athlete_history(self, athlete_name: str) -> pd.DataFrame:
        """Get complete ELO history for a specific athlete."""
        if not self.elo_history:
            self.calculate_elo_ratings()
        
        history_df = pd.DataFrame(self.elo_history)
        athlete_data = history_df[
            history_df['name'].str.lower() == athlete_name.lower()
        ]
        
        return athlete_data.sort_values('date').reset_index(drop=True)
    
    def save_results(self, output_dir: str = "Elo_Data"):
        """Save ELO calculation results."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        if not self.elo_history:
            self.calculate_elo_ratings()
        
        history_df = pd.DataFrame(self.elo_history)
        history_df.to_csv(output_path / "elo_history.csv", index=False)
        
        self.logger.info(f"Saved ELO results to {output_path}")
    
    def load_existing_results(self, output_dir: str = "Elo_Data"):
        """Load existing ELO results from file."""
        output_path = Path(output_dir)
        history_file = output_path / "elo_history.csv"
        
        if not history_file.exists():
            raise FileNotFoundError(f"ELO history file not found: {history_file}")
        
        history_df = pd.read_csv(history_file)
        self.elo_history = history_df.to_dict('records')
        
        # Rebuild current ratings from history
        self.elo_ratings.clear()
        for record in self.elo_history:
            if record['competed']:
                self.elo_ratings[record['name']] = record['elo_after']
    
    def update_elo_ratings(self, new_data: pd.DataFrame) -> pd.DataFrame:
        """Update ELO ratings with new competition data."""
        self.logger.info("Updating ELO ratings with new data...")
        
        # Load existing results if available
        try:
            self.load_existing_results()
            self.logger.info(f"Loaded existing ELO data for {len(self.elo_ratings)} athletes")
        except FileNotFoundError:
            self.logger.info("No existing ELO data found, starting fresh")
            self.elo_ratings.clear()
            self.elo_history.clear()
        
        # Prepare new data
        new_data = new_data.dropna(subset=['round_rank', 'name'])
        new_data = new_data[new_data['name'].str.strip() != '']
        new_data['start_date'] = pd.to_datetime(new_data['start_date'], errors='coerce')
        new_data = new_data.dropna(subset=['start_date'])
        new_data['round_order'] = new_data['round'].map(self.round_priority).fillna(99)
        
        # Sort new data chronologically
        new_data = new_data.sort_values(
            ['start_date', 'event_name', 'round_order', 'round_rank'],
            kind='stable'
        ).reset_index(drop=True)
        
        if new_data.empty:
            self.logger.warning("No valid new competition data to process")
            return pd.DataFrame(self.elo_history)
        
        # Find athletes' first appearances in new data for initialization
        first_appearances = new_data.groupby('name')['start_date'].min()
        
        # Process new competitions chronologically
        for group_key, event_data in new_data.groupby(
            ['event_name', 'start_date', 'discipline', 'gender', 'round'], 
            sort=False
        ):
            event_name, date, discipline, gender, round_type = group_key
            event_data = event_data.sort_values('round_rank')
            
            athletes = event_data['name'].tolist()
            ranks = event_data['round_rank'].tolist()
            
            # Initialize new athletes
            for athlete in athletes:
                if athlete not in self.elo_ratings:
                    self.elo_ratings[athlete] = self.initial_rating
                    first_date = first_appearances[athlete]
                    
                    self.elo_history.append({
                        'name': athlete,
                        'event': 'Initial Rating',
                        'year': first_date.year,
                        'date': first_date,
                        'discipline': discipline,
                        'gender': gender,
                        'round': 'Initial',
                        'rank': None,
                        'elo_before': self.initial_rating,
                        'elo_after': self.initial_rating,
                        'elo_change': 0,
                        'competed': False
                    })
            
            # Calculate ELO changes for this round
            self._process_round(athletes, ranks, event_name, date, discipline, gender, round_type)
        
        # Convert to DataFrame and sort
        result = pd.DataFrame(self.elo_history)
        if not result.empty:
            result = result.sort_values(
                ['date', 'competed', 'name'], 
                kind='stable'
            ).reset_index(drop=True)
        
        # Save updated results
        self.save_results()
        
        self.logger.info(f"Updated ELO for {len(self.elo_ratings)} athletes with {len(new_data)} new records")
        return result
                

# Example usage
if __name__ == "__main__":
    # Initialize calculator
    calculator = ELOCalculator()
    
    # Calculate ELO ratings
    elo_history_df = calculator.calculate_elo_ratings()
    
    # Get current rankings
    top_n = 8
    discipline = "Boulder"
    gender = "Men"
    era_start = "2010-01-01"
    
    current_ranking = calculator.get_current_rankings(discipline=discipline, gender=gender)
    print(f"Top {top_n} {discipline} {gender}:")
    print(current_ranking.head(top_n))
    
    
    # Save results
    calculator.save_results()