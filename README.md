# Port Entity Exporter

A powerful Python CLI for exporting entities from Port. Easily export all entities, filter by blueprint, or select specific entities. Exclude unwanted items and save your data as JSON, YAML, or CSV. Highly configurable for easy integration into your workflows.

## 🚀 Key Features

- **Flexible Export Options**:
  - Export all entities from all blueprints.
  - Export entities from a specific list of blueprints.
  - Export a specific list of entities by their identifiers.
- **Advanced Filtering**:
  - Exclude specific entities from any export.
  - Option to include or exclude calculated properties.
- **Multiple Output Formats**:
  - **JSON**: Perfect for API integrations and machine-to-machine communication.
  - **YAML**: Human-readable format, great for configuration and manual review.
  - **CSV**: Flattened format, ideal for analysis in spreadsheets.
- **Robust and User-Friendly**:
  - Secure credential management using `.env` files.
  - Comprehensive logging for clear progress tracking and troubleshooting.
  - Automatic help generation and input validation.

## ⚙️ Setup and Installation

### 1. Prerequisites
- Python 3.7+

### 2. Clone the Repository
```bash
git clone <repository-url>
cd <repository-name>
```

### 3. Install Dependencies
Install the required Python packages using `pip`:
```bash
pip install -r requirements.txt
```

### 4. Configure Your Port Credentials
Create a `.env` file by copying the provided example and fill in your Port API credentials.

```bash
cp env.example .env
```

Now, open the `.env` file and replace the placeholder values with your actual Port `Client ID` and `Client Secret`.

```dotenv
# .env
PORT_CLIENT_ID=your_port_client_id_here
PORT_CLIENT_SECRET=your_port_client_secret_here
PORT_BASE_URL=https://api.getport.io/v1
```

## 💡 Usage

The script is designed to be run from the command line with various options to control the export process.

### Basic Commands

**View all available options:**
```bash
python port_entity_exporter.py --help
```

### Export Examples

**1. Export all entities from all blueprints (default JSON format):**
```bash
python port_entity_exporter.py --all
```
*This will create a `port_entities.json` file.*

**2. Export entities from specific blueprints:**
```bash
python port_entity_exporter.py --blueprints service,deployment,environment
```

**3. Export specific entities by their identifiers:**
The script will automatically search all blueprints to find the specified entities.
```bash
python port_entity_exporter.py --entities my-service,prod-deployment
```

**4. Export all entities but exclude a few:**
```bash
python port_entity_exporter.py --all --exclude legacy-service,old-deployment
```

### Advanced Usage

**1. Change the output format to YAML:**
```bash
python port_entity_exporter.py --all --format yaml
```
*This will create a `port_entities.yaml` file.*

**2. Specify a custom output file name:**
```bash
python port_entity_exporter.py --all --format csv --output my_entities.csv
```

**3. Exclude calculated properties from the export:**
This can speed up the export process for complex blueprints.
```bash
python port_entity_exporter.py --all --exclude-calculated
```

**4. Enable verbose logging for troubleshooting:**
```bash
python port_entity_exporter.py --all --verbose
```

## 📝 Logging

The script generates a `port_exporter.log` file, which contains detailed information about the export process, including API requests, successes, and any errors encountered. This is useful for auditing and debugging. 