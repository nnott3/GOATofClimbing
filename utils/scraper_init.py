import os
import requests
import json
import re
import pandas as pd
import logging
from typing import Dict, List
from dotenv import load_dotenv
from pathlib import Path
import time

load_dotenv()

class IFSCScraper:
    def __init__(self, log_level: str = "INFO", rate_limit: float = 0.5):
        self.rate_limit = rate_limit

        # --- Setup logging ---
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(getattr(logging, log_level.upper()))
        if not self.logger.handlers:
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

        # --- Load config from environment ---
        headers_env = os.getenv("IFSC_HEADERS", "{}")
        cookies_string = os.getenv("COOKIES_STRING", "")

        try:
            self.HEADERS = json.loads(headers_env) if headers_env != "{}" else {}
        except json.JSONDecodeError:
            self.HEADERS = {}

        self.COOKIES = {}
        if cookies_string:
            for part in cookies_string.split("; "):
                if "=" in part:
                    key, value = part.split("=", 1)
                    self.COOKIES[key] = value

        self.BASE_API = "https://ifsc.results.info/"

        # --- Create data directories ---
        Path('IFSC_Data/API_Event_metadata').mkdir(parents=True, exist_ok=True)
        Path('IFSC_Data/API_Results_Expanded').mkdir(parents=True, exist_ok=True)
    # def __init__(self, log_level: str = "INFO", rate_limit: float = 0.5):
    #     self.rate_limit = rate_limit
    #     self._setup_logging(log_level)
    #     self._load_config()
        
    #     # Create data directories
    #     Path('IFSC_Data/API_Event_metadata').mkdir(parents=True, exist_ok=True)
    #     Path('IFSC_Data/API_Results_Expanded').mkdir(parents=True, exist_ok=True)
    
    # def _setup_logging(self, log_level: str) -> None:
    #     self.logger = logging.getLogger(self.__class__.__name__)
    #     self.logger.setLevel(getattr(logging, log_level.upper()))
        
    #     if not self.logger.handlers:
    #         formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            
    #         console_handler = logging.StreamHandler()
    #         console_handler.setFormatter(formatter)
    #         self.logger.addHandler(console_handler)
    
    # def _load_config(self) -> None:
    #     headers_env = os.getenv("IFSC_HEADERS", "{}")
    #     cookies_string = os.getenv("COOKIES_STRING", "")
        
    #     try:
    #         self.HEADERS = json.loads(headers_env) if headers_env != "{}" else {}
    #     except json.JSONDecodeError:
    #         self.HEADERS = {}
        
    #     self.COOKIES = {}
    #     if cookies_string:
    #         for part in cookies_string.split("; "):
    #             if "=" in part:
    #                 key, value = part.split("=", 1)
    #                 self.COOKIES[key] = value
        
    #     self.BASE_API = "https://ifsc.results.info/"

    def get_api_data(self, endpoint: str = "") -> Dict:
        url = endpoint if endpoint.startswith("http") else self.BASE_API + endpoint.lstrip("/")
        
        try:
            time.sleep(self.rate_limit)
            response = requests.get(url, headers=self.HEADERS, cookies=self.COOKIES, timeout=30)
            response.raise_for_status()
            return response.json() if response.text else {}
            
        except Exception as e:
            self.logger.error(f"API request failed for {url}: {e}")
            return {}

    def get_worldcup_leagues(self) -> pd.DataFrame:
        self.logger.info("Fetching World Cup leagues...")
        
        info_data = self.get_api_data("api/v1/")
        results = []

        for season in info_data.get("seasons", []):
            year = season.get("name")
            if not year:
                continue
                
            for league in season.get("leagues", []):
                league_name = league.get("name", "")
                if "World Cups" in league_name and "Youth" not in league_name:
                    results.append({
                        "year": int(year),
                        "league_name": league_name,
                        "url": league["url"]
                    })

        df = pd.DataFrame(results)
        # df.to_csv("IFSC_Data/all_years_leagues.csv", index=False)
        self.logger.info(f"Found {len(df)} World Cup leagues")
        return df

    def _clean_location(self, event_name: str, year: int, event_url: str) -> str:
        if 1990 < year <= 1997:
            match = re.search(r'-(.*?)\d', event_name)
            return match.group(1).strip() if match else event_name
        elif 1998 <= year <= 2008:
            parts = event_name.split('-')
            return parts[1].split('(')[0].strip() if len(parts) > 1 else event_name
        else:
            # Fetch from API or fallback to parsing
            event_data = self.get_api_data(event_url)
            location = event_data.get('location', '')
            
            if location:
                cleaned = re.sub(r'(WCH|WC|Wc|\d+)', '', location).strip()
                if cleaned:
                    return cleaned
            
            # Fallback parsing
            if 'Qinghai' in event_name:
                return 'Qinghai'
            parts = event_name.split('-')
            return parts[1].split('(')[0].strip() if len(parts) > 1 else "Unknown"

    def _process_disciplines(self, event_data: Dict, base_event: Dict) -> List[Dict]:
        events_list = []
        
        for discipline in event_data.get('d_cats', []):
            parts = discipline.get('name', '').split()
            if len(parts) < 2:
                continue
                
            discipline_name, gender = parts[0], parts[1]
            
            if 1990 < base_event['year'] < 2007:
                events_list.append({
                    **base_event,
                    "discipline": discipline_name.capitalize(),
                    "gender": gender,
                    "event_results": discipline.get('result_url')
                })
            else:
                for round_data in discipline.get('category_rounds', []):
                    events_list.append({
                        **base_event,
                        "discipline": discipline_name.capitalize(),
                        "gender": gender,
                        "round": round_data.get('name', 'Unknown'),
                        "event_results": discipline.get('result_url'),
                        "category_round_results": round_data.get('result_url'),
                    })
        
        return events_list

    def get_events_from_league(self, league_url: str) -> pd.DataFrame:
        self.logger.info(f"Processing league: {league_url}")
        
        data = self.get_api_data(league_url)
        if not data:
            return pd.DataFrame()
        
        year = int(data.get('season', 0))
        all_events = []
        
        for event in data.get('events', []):
            base_event_data = {
                "event_name": event.get('event', ''),
                "event_id": event.get('event_id'),
                "year": year,
                "start_date": event.get('local_start_date', ''),
                "event_results": event.get('result_url'),
            }
            
            base_event_data['location'] = self._clean_location(
                base_event_data['event_name'], year, event.get('url', '')
            )
            
            all_events.extend(self._process_disciplines(event, base_event_data))
        
        if not all_events:
            return pd.DataFrame()
        
        df = pd.DataFrame(all_events)
        column_order = ['event_name', 'event_id', 'year', 'location', 'discipline', 
                       'gender', 'round', 'start_date', 'category_round_results', 'event_results']
        df = df[[col for col in column_order if col in df.columns]]
        
        filename = f"IFSC_Data/API_Event_metadata/{year}_event_meta.csv"
        # df.to_csv(filename, index=False)
        self.logger.info(f"Processed {len(df)} events for {year}")
        return df

    def _create_base_row(self, athlete: Dict, event_meta: Dict) -> Dict:
        base_row = {
            "name": athlete.get('name', ''),
            "country": athlete.get('country', ''),
            "round_rank": int(athlete['rank']) if athlete.get('rank') is not None else None,
            "round_score": " ".join(athlete.get('score', '').split()) if athlete.get('score') else '',
        }
        base_row.update(event_meta)
        return base_row

    def _process_speed_final(self, athlete: Dict, row: Dict) -> Dict:
        for stage in athlete.get('speed_elimination_stages', []):
            stage_name = stage.get('name', '')
            if stage_name:
                row[f"{stage_name}_winner"] = stage.get('winner') == 1
                if stage.get('time'):
                    row[f"{stage_name}_time"] = stage['time'] / 1000
                elif stage.get('score'):
                    row[f"{stage_name}_time"] = stage.get('score')
        return row

    def _process_combined_stages(self, athlete: Dict, row: Dict) -> Dict:
        for stage in athlete.get('combined_stages', []):
            stage_name = stage.get('stage_name', '')
            
            if 'ascents' not in stage:
                if stage.get('stage_score'):
                    row[f"{stage_name}_score"] = stage['stage_score']
                if stage.get('stage_rank'):
                    row[f"{stage_name}_rank"] = stage['stage_rank']
            
            elif stage_name == 'Boulder':
                for ascent in stage.get('ascents', []):
                    digits = ''.join(filter(str.isdigit, ascent.get("route_name", "")))
                    if digits:
                        p = int(digits)
                        row[f"P{p}_Top"] = ascent.get("top_tries", "X") if ascent.get("top") else "X"
                        row[f"P{p}_Zone"] = ascent.get("zone_tries", "X") if ascent.get("zone") else "X"
            
            elif stage_name == 'Lead':
                for ascent in stage.get('ascents', []):
                    digits = ''.join(filter(str.isdigit, ascent.get("route_name", "")))
                    if digits:
                        row[f"Route_{int(digits)}"] = ascent.get("score", "")
        return row

    def _process_lead_pre_2020(self, athlete: Dict, row: Dict) -> Dict:
        scores = athlete.get('score', '')
        if "|" in scores:
            routes = [route.split()[0] for route in scores.split("|")]
            for i, route_score in enumerate(routes, 1):
                row[f"Route_{i}"] = route_score
        elif scores:
            row["Route_1"] = scores.split()[0]
        return row

    def _process_ascents(self, athlete: Dict, event: Dict, row: Dict) -> Dict:
        discipline = event.get('discipline', '')
        
        for ascent in athlete.get('ascents', []):
            route_name = ascent.get("route_name", "")
            digits = ''.join(filter(str.isdigit, route_name))
            
            if discipline == 'Boulder' and digits:
                p = int(digits)
                row[f"P{p}_Top"] = ascent.get("top_tries", "X") if ascent.get("top") else "X"
                row[f"P{p}_Zone"] = ascent.get("zone_tries", "X") if ascent.get("zone") else "X"
                
            elif discipline == 'Lead' and digits:
                p = int(digits)
                row[f"Route_{p}"] = ascent.get("score", "")
                
            elif discipline == 'Speed':
                if ascent.get('time_ms'):
                    row[f"Quali_time_{route_name}"] = ascent['time_ms'] / 1000
                elif ascent.get('dns'):
                    row[f"Quali_time_{route_name}"] = 'DNS'
                elif ascent.get('dnf'):
                    row[f"Quali_time_{route_name}"] = 'DNF'
        return row

    def parse_round_result(self, event: Dict) -> pd.DataFrame:
        year = event.get('year', 0)
        location = event.get('location', 'Unknown')
        discipline = event.get('discipline', 'Unknown')
        gender = event.get('gender', 'Unknown')
        round_name = event.get('round', 'N/A')
        
        if year <= 2006:
            self.logger.info(f"Parsing UIAA: {year} | {location} | {discipline} | {gender}")
            result_url = event.get('event_results')
        else:
            self.logger.info(f"Parsing IFSC: {year} | {location} | {discipline} | {gender} | {round_name}")
            result_url = event.get('category_round_results')
        
        if not result_url:
            return pd.DataFrame()
        
        data = self.get_api_data(result_url)
        if not data or 'cancel' in data.get('event', '').lower():
            return pd.DataFrame()
        
        results = []
        for athlete in data.get('ranking', []):
            row = self._create_base_row(athlete, event)
            
            # Apply discipline-specific parsing
            if year <= 2006:
                pass  # Base data only for UIAA
            elif discipline == 'Speed' and round_name == 'Final':
                row = self._process_speed_final(athlete, row)
            elif discipline == 'Boulder&lead':
                row = self._process_combined_stages(athlete, row)
            elif discipline == 'Lead' and year <= 2019:
                row = self._process_lead_pre_2020(athlete, row)
            else:
                row = self._process_ascents(athlete, event, row)
            
            results.append(row)
        
        if not results:
            return pd.DataFrame()
        
        df = pd.DataFrame(results)
        
        # Save file
        start_date = event.get('start_date', 'no-date')
        if not round_name or round_name.lower() in ['none', 'n/a']:
            round_name = "no-round"
        
        filename = f"{start_date}_{location}_{discipline}_{gender}_{round_name}.csv"
        
        year_dir = Path(f"IFSC_Data/API_Results_Expanded/{year}")
        year_dir.mkdir(exist_ok=True, parents=True)
        print(f'{year_dir}/{filename}')
        # df.to_csv(year_dir / filename, index=False)
        
        self.logger.info(f"Saved {len(df)} results: {filename}")
        return df, filename
    
# if __name__ == "__main__":
#     scraper = IFSCScraper()

#     df_worldcup = scraper.get_worldcup_leagues()    
#     df_worldcup.to_csv("IFSC_Data/all_years_leagues.csv", index=False)

#     df_meta = scraper.get_events_from_league()
    
    
