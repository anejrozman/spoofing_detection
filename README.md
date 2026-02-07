# Geometric Spoofing Detection

## Overview
**Master's Thesis Project**  
This project utilizes **Information Geometry** to detect spoofing anomalies in Limit Order Books (LOB). It builds upon the ABIDES market simulator to model market dynamics and test detection algorithms.

## Setup

1. **Clone the repository**  
   ```bash
   git clone https://github.com/anejrozman/spoofing_detection.git
   ```

2. **Install dependencies**  
   `TODO: Add dependencies here (e.g., pip install -r requirements.txt)`

## Directory Structure
* **`abides_core/`**  
  The ABIDES simulator (Submodule).  
  * *Source:* [GitHub](https://github.com/abides-sim/abides) | *Paper:* [ArXiv](https://arxiv.org/abs/1904.12066)  
  * *Note:* This folder contains the core simulator logic. While it includes native agents and configs, the custom implementations for this thesis are separated into the root `agents/` and `configs/` folders for clarity and distinct contribution tracking.

* **`agents/`**  
  Custom trading agents developed for this thesis (e.g., Spoofing Agents, OBI Agents).

* **`configs/`**  
  Simulation configuration scripts defining market scenarios and agent behaviors.

* **`geometric/`**  
  Core mathematics and logic for the Information Geometry detection framework.

* **`notebooks/`**  
  Jupyter notebooks for analyzing simulation data and evaluating the performance of the detection algorithm.

## Usage

### 1. Run a Market Simulation
Simulations are executed via the `abides.py` script located within the core module.

**Step 1:** Navigate to the simulator directory:
```bash
cd abides_core
```

**Step 2:** Run the simulation using a configuration file:
```bash
python abides.py -c normal_market_config_w_OBI_agents.py -t <STOCK_TICKER> -d <HISTORICAL_DATE> -s <SEED> -l <LOG_DIRECTORY_NAME>
```

**Simulation Outputs:**  
Logs are stored in `abides_core/log/<LOG_DIRECTORY_NAME>`. The simulation generates the following compressed files:

| File Name | Description |
| :--- | :--- |
| **`EXCHANGE_AGENT.bz2`** | Complete event log of the simulation. |
| **`fundamental_<TICKER>.bz2`** | Time series of the fundamental price. |
| **`ORDERBOOK_<TICKER>_FULL.bz2`** | Full snapshot history of the Limit Order Book. |
| **`POV_EXECUTION_AGENT.bz2`** | Summary statistics for the POV Execution agent. |
| **`summary_log.bz2`** | Start/end balances and performance stats for all agents. |

### 2. Run the Detection Algorithm
To apply the detection logic to your simulation data, open the sample notebook:

*   **Location:** `notebooks/sample_detection_algorithm.ipynb`
*   **Instructions:** Follow the steps inside the notebook to load the generated logs and run the geometric detection analysis.
