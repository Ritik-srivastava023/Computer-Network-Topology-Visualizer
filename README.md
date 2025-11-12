# 🖧 Network Topology Visualizer

## 📘 Overview
The **Network Topology Visualizer** is a Python-based project designed to help visualize and simulate different computer network topologies like **Star**, **Ring**, **Bus**, and **Hybrid**.  
It provides an interactive graphical interface where users can create nodes, connect them, and simulate packet transmission between devices.  

This project is especially useful for **Computer Networks students** to understand how devices are connected and how data travels between them.

---

## 🎯 Objective
To provide an interactive and educational tool for visualizing and simulating network topologies, enabling better understanding of how data packets move through different structures.

---

## ⚙️ Technologies Used
| Component | Description |
|------------|-------------|
| **Language** | Python |
| **Libraries** | `tkinter`, `networkx`, `matplotlib`, `json` |
| **Visualization** | `matplotlib` embedded inside `tkinter` GUI |
| **Storage** | JSON files for saving/loading topologies |

---

## 🧩 Features
✅ Create and label nodes (devices)  
✅ Connect nodes to form edges (links)  
✅ Visualize network layout dynamically  
✅ Animate packet transfer between source and destination  
✅ Save and load topologies (`.json` files)  
✅ Drag and reposition nodes freely  

---

## 🧱 Network Topologies Supported
- 🌟 **Star Topology**
- 🔁 **Ring Topology**
- 🚌 **Bus Topology**
- ⚙️ **Hybrid Topology**

You can load any of these using the provided `.json` files.

---

## 📂 Project Structure
```
Network_Topology_Visualizer/
│
├── network_topology_visualizer.py      # Main Python file
├── star_topology.json                  # Sample topology
├── ring_topology.json
├── bus_topology.json
├── hybrid_topology.json
└── README.md                           # Project documentation
```

---

## 🧠 Concepts Demonstrated
- **Graph Theory:** Representing networks as nodes and edges  
- **Shortest Path Algorithm:** Finding optimal packet routes  
- **Network Topologies:** Understanding Star, Ring, Bus, and Hybrid models  
- **GUI Programming:** Creating interactive interfaces with Tkinter  
- **File Handling:** Saving and loading designs using JSON  

---

## 🪄 How to Run

### 1️⃣ Install Dependencies
```bash
pip install networkx matplotlib
```

### 2️⃣ Run the Application
```bash
python network_topology_visualizer.py
```

### 3️⃣ Load a Sample Topology
Use the **Load Topology** button and choose any of the `.json` files (e.g., `star_topology.json`).

---

## 🎥 Usage Instructions
- Click **Add Node** to add computers/devices  
- Click **Add Edge** to connect two nodes  
- Click **Draw Graph** to visualize  
- Select **Source** and **Destination** nodes and click **Animate Packet** to simulate data transfer  
- Use **Save** or **Load Topology** to store and reuse designs  

---

## 🌈 Future Improvements
- Add color-coded packet paths  
- Support TCP/UDP simulation labels  
- Export animations as GIFs  
- Web version using Flask or React  
