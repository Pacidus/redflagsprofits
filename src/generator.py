#!/usr/bin/env python3
"""
Red Flags Profits - Lightweight Generator (Adapted for Existing Templates)
Works with your existing index.html template structure
"""

import json
import csv
import gzip
import shutil
from pathlib import Path
from datetime import datetime
from jinja2 import Environment, FileSystemLoader


class AdaptedLightweightGenerator:
    """Lightweight generator that works with existing template structure"""
    
    def __init__(self):
        self.data_dir = Path("data")
        self.template_dir = Path("src/templates")
        self.static_dir = Path("src/static")
        self.output_dir = Path("docs")
        
        # Setup Jinja2
        self.env = Environment(
            loader=FileSystemLoader(self.template_dir),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        self._add_custom_filters()
    
    def load_data_files(self):
        """Load focused data files and convert to format expected by existing template"""
        data = {}
        
        # Load each focused data file
        data_files = {
            'metrics': 'metrics.json',
            'metadata': 'metadata.json', 
            'timeline': 'timeline.json',
            'equivalencies': 'equivalencies.json',
            'sparklines': 'sparklines.json'
        }
        
        for key, filename in data_files.items():
            file_path = self.data_dir / filename
            if file_path.exists():
                with open(file_path, 'r') as f:
                    data[key] = json.load(f)
                print(f"✅ Loaded {filename} ({file_path.stat().st_size // 1024}KB)")
            else:
                print(f"⚠️  Missing {filename} - using defaults")
                data[key] = self._get_default_data(key)
        
        return data
    
    def generate_site(self):
        """Generate site using existing template structure"""
        print("🏗️  Generating lightweight site with existing templates...")
        
        # Load focused data files
        raw_data = self.load_data_files()
        
        # Convert to format expected by existing template
        dashboard_data = self._convert_to_dashboard_format(raw_data)
        
        # Create output directory and copy static files
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._copy_static_files()
        
        # Generate optimized data files for web consumption
        self._generate_web_data_files(raw_data)
        
        # Generate main page using existing template
        self._generate_index_with_existing_template(dashboard_data, raw_data)
        
        # Generate compressed versions
        self._compress_files()
        
        print("✅ Lightweight site generation complete!")
        print(f"📁 Output: {self.output_dir.absolute()}")
        return True
    
    def _convert_to_dashboard_format(self, raw_data):
        """Convert focused data files to format expected by existing template"""
        metrics = raw_data.get('metrics', {})
        metadata = raw_data.get('metadata', {})
        timeline = raw_data.get('timeline', [])
        
        # Convert dates
        data_start_date = self._parse_date(metadata.get('data_start_date'))
        data_end_date = self._parse_date(metadata.get('data_end_date'))
        
        # Prepare chart data in format expected by existing template
        wealth_timeline_chart_data = {
            "data": [
                {"x": point.get("date"), "y": point.get("total_wealth", 0)}
                for point in timeline
            ],
            "title": "Total Billionaire Wealth",
            "yAxisTitle": "Wealth (Trillions USD)",
            "summary": {
                "dataPoints": metadata.get('data_points', len(timeline)),
                "timespan": f"{metadata.get('data_start_date', '')} to {metadata.get('data_end_date', '')}",
                "totalIncrease": metrics.get('changes', {}).get('wealth_pct', 0),
                "growthRate": metrics.get('growth_rate', 0),
                "startValue": timeline[0].get('total_wealth', 0) if timeline else 0,
                "endValue": timeline[-1].get('total_wealth', 0) if timeline else 0,
                "exponentialGrowthRate": metrics.get('growth_rate', 0)
            },
            "animation": {"pointDelay": 10, "trendLineSpeed": 1500},
            "timeRange": {
                "start": metadata.get('data_start_date', ''),
                "end": metadata.get('data_end_date', ''),
                "totalDays": metadata.get('data_days_span', 0)
            }
        }
        
        # Build dashboard data in format expected by existing template
        dashboard_data = {
            # Current metrics
            'billionaire_count': metrics.get('billionaire_count', 0),
            'total_wealth_trillions': metrics.get('total_wealth', 0),
            'average_wealth_billions': metrics.get('average_wealth', 0),
            
            # Growth metrics
            'growth_rate': metrics.get('growth_rate', 0),
            'doubling_time': metrics.get('doubling_time', 0),
            'daily_accumulation': metrics.get('daily_accumulation', 0),
            
            # Changes
            'wealth_increase_pct': metrics.get('changes', {}).get('wealth_pct', 0),
            'billionaire_increase_count': metrics.get('changes', {}).get('count_change', 0),
            'avg_wealth_increase_pct': metrics.get('changes', {}).get('avg_pct', 0),
            
            # Dates and metadata
            'data_start_date': data_start_date,
            'data_end_date': data_end_date,
            'data_days_span': metadata.get('data_days_span', 0),
            'data_points': metadata.get('data_points', 0),
            
            # Time series (for existing chart components)
            'time_series': timeline,
            
            # Charts data (for existing chart components)
            'charts': {
                'wealth_timeline': wealth_timeline_chart_data
            },
            
            # Background sparklines (for existing metric cards)
            'background_sparklines': self._generate_background_sparklines(raw_data.get('sparklines', {}))
        }
        
        return dashboard_data
    
    def _generate_background_sparklines(self, sparklines_data):
        """Generate SVG data URIs for background sparklines (compatible with existing cards)"""
        if not sparklines_data:
            return {}
        
        sparklines = {}
        
        for metric in ['wealth', 'count', 'average']:
            if metric in sparklines_data and sparklines_data[metric]:
                svg_data = self._create_sparkline_svg_data_uri(
                    sparklines_data[metric], 
                    sparklines_data.get('bounds', {}).get(metric, {})
                )
                # Map to names expected by existing template
                if metric == 'wealth':
                    sparklines['total_wealth'] = svg_data
                elif metric == 'count':
                    sparklines['billionaire_count'] = svg_data
                elif metric == 'average':
                    sparklines['average_wealth'] = svg_data
        
        return sparklines
    
    def _create_sparkline_svg_data_uri(self, values, bounds):
        """Create SVG data URI for sparkline background"""
        if not values or len(values) < 2:
            return None
            
        width, height = 280, 120
        min_val = bounds.get('min', min(values))
        max_val = bounds.get('max', max(values))
        range_val = max_val - min_val if max_val > min_val else 1
        
        # Create points
        points = []
        for i, val in enumerate(values):
            x = (i / (len(values) - 1)) * width
            y = height - ((val - min_val) / range_val) * (height - 20) - 10
            points.append(f"{x:.1f},{y:.1f}")
        
        polyline_points = " ".join(points)
        
        # Create polygon for filled area
        polygon_points = f"0,{height} " + polyline_points + f" {width},{height}"
        
        svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}">
  <rect width="100%" height="100%" fill="#404040"/>
  <polygon points="{polygon_points}" fill="#1a1a1a" stroke="none"/>
</svg>'''
        
        # Convert to data URI
        import urllib.parse
        return f"data:image/svg+xml,{urllib.parse.quote(svg)}"
    
    def _generate_web_data_files(self, data):
        """Generate optimized data files for web consumption"""
        web_data_dir = self.output_dir / "data"
        web_data_dir.mkdir(exist_ok=True)
        
        # Generate ultra-light CSV timeline (for optional JS charts)
        if 'timeline' in data and data['timeline']:
            self._generate_timeline_csv(data['timeline'], web_data_dir)
        
        # Generate minified JSON files
        for key in ['metrics', 'sparklines', 'equivalencies']:
            if key in data:
                self._generate_minified_json(data[key], web_data_dir / f"{key}.json")
    
    def _generate_timeline_csv(self, timeline_data, output_dir):
        """Generate ultra-light CSV file for timeline chart"""
        csv_file = output_dir / "timeline.csv"
        
        with open(csv_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['date', 'wealth', 'count'])
            
            for point in timeline_data:
                # Round to 1 decimal to save space
                wealth = round(point.get('total_wealth', 0), 1)
                count = int(point.get('billionaire_count', 0))
                writer.writerow([point['date'], wealth, count])
        
        size_kb = csv_file.stat().st_size // 1024
        print(f"📊 Generated timeline.csv ({size_kb}KB)")
    
    def _generate_minified_json(self, data, output_file):
        """Generate minified JSON files"""
        with open(output_file, 'w') as f:
            json.dump(data, f, separators=(',', ':'))  # No spaces for minimal size
        
        size_kb = output_file.stat().st_size // 1024
        print(f"📄 Generated {output_file.name} ({size_kb}KB)")
    
    def _copy_static_files(self):
        """Copy CSS, JS, and assets to output directory"""
        for subdir in ["css", "js", "assets"]:
            src_dir = self.static_dir / subdir
            dst_dir = self.output_dir / subdir
            
            if src_dir.exists():
                if dst_dir.exists():
                    shutil.rmtree(dst_dir)
                shutil.copytree(src_dir, dst_dir)
                
                # Calculate total size
                total_size = sum(f.stat().st_size for f in dst_dir.rglob('*') if f.is_file())
                print(f"📁 Copied {subdir}/ ({total_size // 1024}KB)")
    
    def _generate_index_with_existing_template(self, dashboard_data, raw_data):
        """Generate index.html using existing template"""
        template = self.env.get_template("index.html")
        
        # Prepare context in format expected by existing template
        context = {
            'page_title': "Red Flags Profits - Wealth Monopolization Analysis",
            'dashboard': dashboard_data,
            'analysis': {
                'wealth_equivalencies': raw_data.get('equivalencies', []),
                'growth_metrics': {
                    'real_growth_rate': dashboard_data['growth_rate'],
                    'inflation_adjusted': True,
                    'acceleration': 'increasing' if dashboard_data['growth_rate'] > 8.0 else 'stable'
                }
            },
            'last_updated': self._format_timestamp(raw_data.get('metadata', {}).get('last_updated')),
        }
        
        # Render template
        html_content = template.render(**context)
        
        # Write to file
        with open(self.output_dir / "index.html", "w", encoding="utf-8") as f:
            f.write(html_content)
        
        size_kb = len(html_content.encode('utf-8')) // 1024
        print(f"📄 Generated index.html ({size_kb}KB)")
    
    def _compress_files(self):
        """Generate gzipped versions of key files"""
        files_to_compress = [
            'index.html',
            'css/main.css',
            'css/components.css', 
            'data/timeline.csv'
        ]
        
        total_savings = 0
        for file_path in files_to_compress:
            full_path = self.output_dir / file_path
            if full_path.exists():
                original_size = full_path.stat().st_size
                
                with open(full_path, 'rb') as f_in:
                    with gzip.open(str(full_path) + '.gz', 'wb') as f_out:
                        f_out.write(f_in.read())
                
                compressed_size = Path(str(full_path) + '.gz').stat().st_size
                savings = original_size - compressed_size
                total_savings += savings
        
        print(f"🗜️  Compressed files (saved {total_savings // 1024}KB)")
    
    def _parse_date(self, date_str):
        """Parse date string to datetime object"""
        if not date_str:
            return datetime.now()
        
        try:
            if 'T' in str(date_str):
                return datetime.fromisoformat(str(date_str).replace('Z', '+00:00'))
            else:
                return datetime.strptime(str(date_str), '%Y-%m-%d')
        except:
            return datetime.now()
    
    def _format_timestamp(self, timestamp_str):
        """Format timestamp for display"""
        if not timestamp_str:
            return datetime.now().strftime("%Y-%m-%d %H:%M UTC")
        
        try:
            dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            return dt.strftime("%Y-%m-%d %H:%M UTC")
        except:
            return str(timestamp_str)
    
    def _get_default_data(self, key):
        """Get default data for missing files"""
        defaults = {
            'metrics': {
                "billionaire_count": 2756,
                "total_wealth": 14.2,
                "average_wealth": 5.2,
                "growth_rate": 15.2,
                "doubling_time": 4.6,
                "daily_accumulation": 0.8,
                "changes": {
                    "wealth_pct": 28.4,
                    "count_change": 157,
                    "avg_pct": 12.8
                }
            },
            'metadata': {
                "last_updated": datetime.now().isoformat(),
                "data_start_date": "2024-01-01",
                "data_end_date": datetime.now().strftime('%Y-%m-%d'),
                "data_points": 365,
                "data_days_span": 365
            },
            'equivalencies': [
                {
                    "comparison": "Median US Households",
                    "value": "215 million",
                    "context": "Annual household income"
                }
            ],
            'sparklines': {
                "wealth": [11.1, 11.6, 12.1, 12.8, 13.4, 14.2],
                "count": [2599, 2615, 2635, 2675, 2715, 2756],
                "average": [4.3, 4.4, 4.6, 4.8, 5.0, 5.2],
                "bounds": {
                    "wealth": {"min": 11.1, "max": 14.2},
                    "count": {"min": 2599, "max": 2756},
                    "average": {"min": 4.3, "max": 5.2}
                }
            },
            'timeline': []
        }
        return defaults.get(key, {})
    
    def _add_custom_filters(self):
        """Add custom Jinja2 filters"""
        filter_map = {
            'number': lambda value, precision=1: f"{value:,.{precision}f}" if isinstance(value, (int, float)) else str(value),
            'currency': lambda value, precision=1: f"${value:.{precision}f}" if isinstance(value, (int, float)) else str(value),
            'percentage': lambda value, precision=1: f"{value:+.{precision}f}%" if isinstance(value, (int, float)) else str(value),
            'date': lambda date_obj, format_str="%B %d, %Y": date_obj.strftime(format_str) if hasattr(date_obj, 'strftime') else str(date_obj),
        }
        
        for name, func in filter_map.items():
            self.env.filters[name] = func
