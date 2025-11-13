import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import networkx as nx
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyBboxPatch, Rectangle, Wedge
from matplotlib.collections import LineCollection
import json
import numpy as np
import random

# Device type configurations
DEVICE_TYPES = {
    'Router': {'color': '#4A90E2', 'shape': 'circle', 'icon': '🔀'},
    'Switch': {'color': '#50C878', 'shape': 'square', 'icon': '🔌'},
    'Hub': {'color': '#FFB347', 'shape': 'square', 'icon': '⚡'},
    'Computer': {'color': '#9370DB', 'shape': 'rect', 'icon': '💻'},
    'Server': {'color': '#E74C3C', 'shape': 'rect', 'icon': '🖥️'}
}

# Cable type configurations
CABLE_TYPES = {
    'Ethernet': {'color': '#666666', 'style': 'solid', 'width': 2.5, 'speed': 1.0},
    'Fiber Optic': {'color': '#FFD700', 'style': 'solid', 'width': 3.0, 'speed': 1.5},
    'Wireless': {'color': '#87CEEB', 'style': 'dashed', 'width': 2.0, 'speed': 0.8}
}

def default_node_label(n):
    return f"N{n}"

class NetworkVisualizerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Advanced Network Topology Visualizer")
        
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        
        window_width = int(screen_width * 0.85)
        window_height = int(screen_height * 0.85)
        self.root.geometry(f"{window_width}x{window_height}")
        
        self.G = nx.Graph()
        self.pos = {}
        self.node_count = 0
        self.selected_node = None
        self.dragging = False
        self.animating = False
        self.animation_frame = 0
        self.packet_trail = []
        
        # Enhanced attributes
        self.node_devices = {}  # node -> device type
        self.node_ips = {}  # node -> IP address
        self.edge_cables = {}  # (node1, node2) -> cable type
        self.packet_loss_rate = 0.0  # 0.0 to 1.0
        
        # Animation parameters
        self.animation_speed = 80
        self.frames_per_edge = 20
        
        # Create main container
        main_container = ttk.Frame(root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        main_container.grid_columnconfigure(0, weight=1)
        main_container.grid_rowconfigure(0, weight=1)
        
        # Matplotlib figure
        fig_width = max(12, window_width // 100)
        fig_height = max(9, window_height // 100)
        self.fig, self.ax = plt.subplots(figsize=(fig_width, fig_height))
        self.fig.patch.set_facecolor('#f0f0f0')
        self.ax.set_facecolor('#ffffff')
        plt.tight_layout()
        
        # Canvas
        canvas_frame = ttk.Frame(main_container)
        canvas_frame.grid(row=0, column=0, sticky='nsew', padx=(0, 10))
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=canvas_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.canvas.mpl_connect('button_press_event', self.on_click)
        self.canvas.mpl_connect('button_release_event', self.on_release)
        self.canvas.mpl_connect('motion_notify_event', self.on_motion)

        # Enhanced control panel with notebook (tabs)
        ctrlframe = ttk.Frame(main_container, padding=10)
        ctrlframe.grid(row=0, column=1, sticky='nsew')
        
        # Style
        style = ttk.Style()
        style.configure('Title.TLabel', font=('Segoe UI', 14, 'bold'))
        style.configure('Section.TLabel', font=('Segoe UI', 11, 'bold'))
        style.configure('TButton', padding=8, font=('Segoe UI', 10))

        # Title
        ttk.Label(ctrlframe, text='🌐 Network Control Panel', 
                 style='Title.TLabel').grid(row=0, column=0, columnspan=2, pady=(0,10))

        # Create notebook for tabs
        self.notebook = ttk.Notebook(ctrlframe)
        self.notebook.grid(row=1, column=0, columnspan=2, sticky='nsew', pady=(0,10))
        
        # Configure grid weight
        ctrlframe.grid_rowconfigure(1, weight=1)
        
        # Create tabs
        self.create_topology_tab()
        self.create_device_tab()
        self.create_simulation_tab()
        self.create_file_tab()

        # Initial draw
        self.redraw()

    def create_topology_tab(self):
        tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(tab, text='Topology')
        
        # Node controls
        ttk.Label(tab, text='Node Controls', style='Section.TLabel').grid(
            row=0, column=0, columnspan=2, pady=(0,8))
        
        ttk.Button(tab, text='➕ Add Node', command=self.add_node).grid(
            row=1, column=0, sticky='ew', padx=(0,5), pady=3)
        ttk.Button(tab, text='➖ Remove Node', command=self.remove_selected_node).grid(
            row=1, column=1, sticky='ew', pady=3)

        ttk.Separator(tab, orient='horizontal').grid(
            row=2, column=0, columnspan=2, sticky='ew', pady=10)

        # Edge controls
        ttk.Label(tab, text='Connection Management', style='Section.TLabel').grid(
            row=3, column=0, columnspan=2, pady=(0,8))
        
        ttk.Label(tab, text='From:').grid(row=4, column=0, sticky='w', pady=2)
        ttk.Label(tab, text='To:').grid(row=4, column=1, sticky='w', pady=2)
        
        self.edge_a = tk.StringVar()
        self.edge_b = tk.StringVar()
        self.edge_a_cb = ttk.Combobox(tab, textvariable=self.edge_a, 
                                       state='readonly', width=10, font=('Segoe UI', 9))
        self.edge_b_cb = ttk.Combobox(tab, textvariable=self.edge_b, 
                                       state='readonly', width=10, font=('Segoe UI', 9))
        self.edge_a_cb.grid(row=5, column=0, pady=3, padx=(0,5))
        self.edge_b_cb.grid(row=5, column=1, pady=3)
        
        # Cable type selection
        ttk.Label(tab, text='Cable Type:').grid(row=6, column=0, columnspan=2, sticky='w', pady=(5,2))
        self.cable_type = tk.StringVar(value='Ethernet')
        cable_frame = ttk.Frame(tab)
        cable_frame.grid(row=7, column=0, columnspan=2, sticky='ew', pady=3)
        
        for i, cable in enumerate(CABLE_TYPES.keys()):
            ttk.Radiobutton(cable_frame, text=cable, variable=self.cable_type, 
                          value=cable).pack(anchor='w', pady=2)
        
        ttk.Button(tab, text='🔗 Add Connection', command=self.add_edge).grid(
            row=8, column=0, sticky='ew', padx=(0,5), pady=5)
        ttk.Button(tab, text='✂️ Remove Connection', command=self.remove_edge).grid(
            row=8, column=1, sticky='ew', pady=5)

    def create_device_tab(self):
        tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(tab, text='Devices')
        
        ttk.Label(tab, text='Device Configuration', style='Section.TLabel').grid(
            row=0, column=0, columnspan=2, pady=(0,8))
        
        # Device type selection
        ttk.Label(tab, text='Device Type:').grid(row=1, column=0, columnspan=2, sticky='w', pady=(5,2))
        self.device_type = tk.StringVar(value='Router')
        
        for i, (device, config) in enumerate(DEVICE_TYPES.items()):
            row = 2 + i
            ttk.Radiobutton(tab, text=f"{config['icon']} {device}", 
                          variable=self.device_type, value=device).grid(
                row=row, column=0, columnspan=2, sticky='w', pady=2)
        
        ttk.Separator(tab, orient='horizontal').grid(
            row=7, column=0, columnspan=2, sticky='ew', pady=10)
        
        # IP Address configuration
        ttk.Label(tab, text='IP Address Management', style='Section.TLabel').grid(
            row=8, column=0, columnspan=2, pady=(0,8))
        
        ttk.Label(tab, text='Selected Node:').grid(row=9, column=0, sticky='w', pady=2)
        self.ip_node_var = tk.StringVar()
        self.ip_node_cb = ttk.Combobox(tab, textvariable=self.ip_node_var, 
                                        state='readonly', width=12)
        self.ip_node_cb.grid(row=9, column=1, pady=2)
        
        ttk.Label(tab, text='IP Address:').grid(row=10, column=0, sticky='w', pady=2)
        self.ip_entry = ttk.Entry(tab, width=14)
        self.ip_entry.grid(row=10, column=1, pady=2)
        self.ip_entry.insert(0, '192.168.1.1')
        
        ttk.Button(tab, text='🔢 Set IP Address', command=self.set_ip_address).grid(
            row=11, column=0, columnspan=2, sticky='ew', pady=5)
        
        ttk.Button(tab, text='🔄 Auto-Assign IPs', command=self.auto_assign_ips).grid(
            row=12, column=0, columnspan=2, sticky='ew', pady=3)
        
        # Display current IPs
        ttk.Label(tab, text='Current IP Assignments:', font=('Segoe UI', 9, 'bold')).grid(
            row=13, column=0, columnspan=2, sticky='w', pady=(10,5))
        
        ip_list_frame = ttk.Frame(tab)
        ip_list_frame.grid(row=14, column=0, columnspan=2, sticky='nsew', pady=5)
        
        self.ip_listbox = tk.Listbox(ip_list_frame, height=8, font=('Courier', 9))
        scrollbar = ttk.Scrollbar(ip_list_frame, orient='vertical', command=self.ip_listbox.yview)
        self.ip_listbox.configure(yscrollcommand=scrollbar.set)
        
        self.ip_listbox.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

    def create_simulation_tab(self):
        tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(tab, text='Simulation')
        
        # Packet simulation
        ttk.Label(tab, text='Packet Simulation', style='Section.TLabel').grid(
            row=0, column=0, columnspan=2, pady=(0,8))
        
        ttk.Label(tab, text='Source:').grid(row=1, column=0, sticky='w', pady=2)
        ttk.Label(tab, text='Destination:').grid(row=1, column=1, sticky='w', pady=2)
        
        self.src_var = tk.StringVar()
        self.dst_var = tk.StringVar()
        self.src_cb = ttk.Combobox(tab, textvariable=self.src_var, 
                                    state='readonly', width=10, font=('Segoe UI', 9))
        self.dst_cb = ttk.Combobox(tab, textvariable=self.dst_var, 
                                    state='readonly', width=10, font=('Segoe UI', 9))
        self.src_cb.grid(row=2, column=0, pady=3, padx=(0,5))
        self.dst_cb.grid(row=2, column=1, pady=3)
        
        ttk.Separator(tab, orient='horizontal').grid(
            row=3, column=0, columnspan=2, sticky='ew', pady=10)
        
        # Packet loss configuration
        ttk.Label(tab, text='Network Conditions', style='Section.TLabel').grid(
            row=4, column=0, columnspan=2, pady=(0,8))
        
        ttk.Label(tab, text='Packet Loss Rate (%):').grid(
            row=5, column=0, columnspan=2, sticky='w', pady=2)
        
        self.loss_var = tk.DoubleVar(value=0.0)
        loss_frame = ttk.Frame(tab)
        loss_frame.grid(row=6, column=0, columnspan=2, sticky='ew', pady=5)
        
        self.loss_scale = ttk.Scale(loss_frame, from_=0, to=50, 
                                    variable=self.loss_var, orient='horizontal')
        self.loss_scale.pack(side='left', fill='x', expand=True, padx=(0,5))
        
        self.loss_label = ttk.Label(loss_frame, text='0%', width=6)
        self.loss_label.pack(side='right')
        
        self.loss_scale.configure(command=lambda v: self.loss_label.configure(
            text=f'{float(v):.1f}%'))
        
        ttk.Separator(tab, orient='horizontal').grid(
            row=7, column=0, columnspan=2, sticky='ew', pady=10)
        
        # Simulation mode
        ttk.Label(tab, text='Simulation Mode:', font=('Segoe UI', 10, 'bold')).grid(
            row=8, column=0, columnspan=2, sticky='w', pady=(0,5))
        
        self.sim_mode = tk.StringVar(value='unicast')
        ttk.Radiobutton(tab, text='🎯 Unicast (Direct)', 
                       variable=self.sim_mode, value='unicast').grid(
            row=9, column=0, columnspan=2, sticky='w', pady=2)
        ttk.Radiobutton(tab, text='📡 Broadcast (All nodes)', 
                       variable=self.sim_mode, value='broadcast').grid(
            row=10, column=0, columnspan=2, sticky='w', pady=2)
        
        ttk.Separator(tab, orient='horizontal').grid(
            row=11, column=0, columnspan=2, sticky='ew', pady=10)
        
        # Animation controls
        ttk.Button(tab, text='🚀 Start Simulation', 
                  command=self.start_animation).grid(
            row=12, column=0, columnspan=2, sticky='ew', pady=3)
        
        ttk.Button(tab, text='⏹️ Stop Simulation', 
                  command=self.stop_animation).grid(
            row=13, column=0, columnspan=2, sticky='ew', pady=3)
        
        # Simulation log
        ttk.Label(tab, text='Simulation Log:', font=('Segoe UI', 9, 'bold')).grid(
            row=14, column=0, columnspan=2, sticky='w', pady=(10,5))
        
        log_frame = ttk.Frame(tab)
        log_frame.grid(row=15, column=0, columnspan=2, sticky='nsew', pady=5)
        
        self.log_text = tk.Text(log_frame, height=8, font=('Courier', 8), wrap='word')
        log_scrollbar = ttk.Scrollbar(log_frame, orient='vertical', 
                                      command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scrollbar.set)
        
        self.log_text.pack(side='left', fill='both', expand=True)
        log_scrollbar.pack(side='right', fill='y')

    def create_file_tab(self):
        tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(tab, text='File')
        
        ttk.Label(tab, text='File Operations', style='Section.TLabel').grid(
            row=0, column=0, columnspan=2, pady=(0,8))
        
        ttk.Button(tab, text='💾 Save Topology', command=self.save_topology).grid(
            row=1, column=0, columnspan=2, sticky='ew', pady=3)
        ttk.Button(tab, text='📂 Load Topology', command=self.load_topology).grid(
            row=2, column=0, columnspan=2, sticky='ew', pady=3)
        
        ttk.Separator(tab, orient='horizontal').grid(
            row=3, column=0, columnspan=2, sticky='ew', pady=10)
        
        ttk.Label(tab, text='Network Statistics', style='Section.TLabel').grid(
            row=4, column=0, columnspan=2, pady=(0,8))
        
        self.stats_text = tk.Text(tab, height=12, font=('Courier', 9), wrap='word')
        self.stats_text.grid(row=5, column=0, columnspan=2, sticky='nsew', pady=5)
        
        ttk.Button(tab, text='📊 Update Statistics', command=self.update_statistics).grid(
            row=6, column=0, columnspan=2, sticky='ew', pady=3)
        
        ttk.Separator(tab, orient='horizontal').grid(
            row=7, column=0, columnspan=2, sticky='ew', pady=10)
        
        # Legend
        ttk.Label(tab, text='💡 Legend', font=('Segoe UI', 10, 'bold')).grid(
            row=8, column=0, columnspan=2, sticky='w', pady=(0,5))
        
        legend_text = (
            "🔀 Router - Routes packets\n"
            "🔌 Switch - Smart forwarding\n"
            "⚡ Hub - Broadcasts all data\n"
            "💻 Computer - End device\n"
            "🖥️ Server - Network server\n\n"
            "━━ Ethernet (1x speed)\n"
            "━━ Fiber Optic (1.5x)\n"
            "- - Wireless (0.8x)"
        )
        legend_label = ttk.Label(tab, text=legend_text, justify=tk.LEFT, 
                               font=('Segoe UI', 8))
        legend_label.grid(row=9, column=0, columnspan=2, sticky='w', pady=5)

    # ---------- Topology editing ----------
    def add_node(self):
        self.node_count += 1
        nid = default_node_label(self.node_count)
        self.G.add_node(nid)
        
        # Set default device type and IP
        self.node_devices[nid] = self.device_type.get()
        
        # Better initial positioning
        angle = 2 * np.pi * len(self.pos) / max(8, len(self.pos) + 1)
        radius = 0.5
        self.pos[nid] = (radius * np.cos(angle), radius * np.sin(angle))
        
        self.update_comboboxes()
        self.update_ip_display()
        self.redraw()
        self.log(f"Added {self.node_devices[nid]} node: {nid}")

    def remove_selected_node(self):
        if self.selected_node and self.selected_node in self.G.nodes:
            node = self.selected_node
            self.G.remove_node(node)
            self.pos.pop(node, None)
            self.node_devices.pop(node, None)
            self.node_ips.pop(node, None)
            
            # Remove edge cables
            edges_to_remove = []
            for edge in list(self.edge_cables.keys()):
                if node in edge:
                    edges_to_remove.append(edge)
            for edge in edges_to_remove:
                self.edge_cables.pop(edge, None)
            
            self.selected_node = None
            self.update_comboboxes()
            self.update_ip_display()
            self.redraw()
            self.log(f"Removed node: {node}")
        else:
            messagebox.showinfo('Remove Node', 
                              'Select a node on the canvas first.')

    def add_edge(self):
        a = self.edge_a.get()
        b = self.edge_b.get()
        if not a or not b:
            messagebox.showwarning('Add Connection', 'Choose two nodes.')
            return
        if a == b:
            messagebox.showwarning('Add Connection', 'Choose two different nodes.')
            return
        
        self.G.add_edge(a, b)
        cable = self.cable_type.get()
        self.edge_cables[(a, b)] = cable
        self.edge_cables[(b, a)] = cable  # Bidirectional
        
        self.redraw()
        self.log(f"Connected {a} ⟷ {b} via {cable}")

    def remove_edge(self):
        a = self.edge_a.get()
        b = self.edge_b.get()
        if not a or not b:
            messagebox.showwarning('Remove Connection', 'Choose two nodes.')
            return
        if self.G.has_edge(a, b):
            self.G.remove_edge(a, b)
            self.edge_cables.pop((a, b), None)
            self.edge_cables.pop((b, a), None)
            self.redraw()
            self.log(f"Removed connection: {a} ⟷ {b}")
        else:
            messagebox.showinfo('Remove Connection', 'Connection does not exist.')

    def set_ip_address(self):
        node = self.ip_node_var.get()
        ip = self.ip_entry.get().strip()
        
        if not node:
            messagebox.showwarning('Set IP', 'Select a node first.')
            return
        
        if not self.validate_ip(ip):
            messagebox.showwarning('Invalid IP', 
                                 'Please enter a valid IP address (e.g., 192.168.1.1)')
            return
        
        self.node_ips[node] = ip
        self.update_ip_display()
        self.redraw()
        self.log(f"Set IP for {node}: {ip}")

    def auto_assign_ips(self):
        base_ip = "192.168.1."
        counter = 1
        
        for node in sorted(self.G.nodes):
            self.node_ips[node] = f"{base_ip}{counter}"
            counter += 1
        
        self.update_ip_display()
        self.redraw()
        self.log(f"Auto-assigned IPs to {len(self.node_ips)} nodes")

    def validate_ip(self, ip):
        parts = ip.split('.')
        if len(parts) != 4:
            return False
        try:
            return all(0 <= int(p) <= 255 for p in parts)
        except:
            return False

    def update_comboboxes(self):
        nodes = sorted(list(self.G.nodes))
        for cb in (self.edge_a_cb, self.edge_b_cb, self.src_cb, 
                   self.dst_cb, self.ip_node_cb):
            cb['values'] = nodes
            val = cb.get()
            if val not in nodes:
                cb.set('')

    def update_ip_display(self):
        self.ip_listbox.delete(0, tk.END)
        for node in sorted(self.G.nodes):
            ip = self.node_ips.get(node, 'Not set')
            device = self.node_devices.get(node, 'Router')
            self.ip_listbox.insert(tk.END, f"{node}: {ip} ({device})")

    def log(self, message):
        if hasattr(self, 'log_text'):
            self.log_text.insert(tk.END, f"{message}\n")
            self.log_text.see(tk.END)

    # ---------- Enhanced Drawing ----------
    def redraw(self, highlight_path=None, packet_pos=None, pulse_nodes=None, 
               rejected_nodes=None, broadcast_nodes=None):
        self.ax.clear()
        self.ax.set_xticks([])
        self.ax.set_yticks([])
        self.ax.set_xlim(-1.2, 1.2)
        self.ax.set_ylim(-1.2, 1.2)
        
        if not self.pos and len(self.G) > 0:
            self.pos = nx.spring_layout(self.G, k=0.5, iterations=50)
        
        if len(self.G) == 0:
            self.ax.text(0, 0, 'Click "Add Node" to start building your network',
                        ha='center', va='center', fontsize=14, color='gray')
            self.canvas.draw_idle()
            return

        # Draw edges with cable types
        for edge in self.G.edges:
            cable_type = self.edge_cables.get(edge, 'Ethernet')
            cable_config = CABLE_TYPES[cable_type]
            
            x = [self.pos[edge[0]][0], self.pos[edge[1]][0]]
            y = [self.pos[edge[0]][1], self.pos[edge[1]][1]]
            
            color = cable_config['color']
            width = cable_config['width']
            style = cable_config['style']
            
            # Highlight path edges
            if highlight_path and len(highlight_path) >= 2:
                path_edges = list(zip(highlight_path, highlight_path[1:]))
                if edge in path_edges or (edge[1], edge[0]) in path_edges:
                    color = '#ff4444'
                    width = 4.0
            
            self.ax.plot(x, y, color=color, linewidth=width,
                        linestyle=style, zorder=1, alpha=0.7)

        # Draw nodes with device types
        for node in self.G.nodes:
            x, y = self.pos[node]
            
            device_type = self.node_devices.get(node, 'Router')
            device_config = DEVICE_TYPES[device_type]
            
            color = device_config['color']
            shape = device_config['shape']
            icon = device_config['icon']
            
            base_size = 0.05
            edge_color = '#2E5C8A'
            
            if node == self.selected_node:
                color = '#FF9500'
                edge_color = '#CC7700'
                base_size = 0.06
            
            # Special highlighting for broadcast/rejected nodes
            if rejected_nodes and node in rejected_nodes:
                # Red X overlay for rejected packets
                self.ax.plot([x-0.04, x+0.04], [y-0.04, y+0.04], 
                           'r-', linewidth=3, zorder=10)
                self.ax.plot([x-0.04, x+0.04], [y+0.04, y-0.04], 
                           'r-', linewidth=3, zorder=10)
            
            if broadcast_nodes and node in broadcast_nodes:
                # Green checkmark for accepting node
                self.ax.plot([x-0.02, x, x+0.04], [y, y-0.03, y+0.05], 
                           'g-', linewidth=3, zorder=10)
            
            # Pulse effect
            pulse_factor = 1.0
            if pulse_nodes and node in pulse_nodes:
                pulse_factor = 1.0 + 0.3 * np.sin(self.animation_frame * 0.3)
                glow = Circle((x, y), base_size * 1.5 * pulse_factor, 
                            color=color, alpha=0.3, zorder=2)
                self.ax.add_patch(glow)
            
            # Draw device shape
            if shape == 'circle':
                circle = Circle((x, y), base_size * pulse_factor, 
                              color=color, ec=edge_color, linewidth=2.5, zorder=3)
                self.ax.add_patch(circle)
            elif shape == 'square':
                size = base_size * 2 * pulse_factor
                square = Rectangle((x-base_size*pulse_factor, y-base_size*pulse_factor), 
                                  size, size,
                                  color=color, ec=edge_color, linewidth=2.5, zorder=3)
                self.ax.add_patch(square)
            elif shape == 'rect':
                width = base_size * 1.5 * pulse_factor
                height = base_size * 1.2 * pulse_factor
                rect = Rectangle((x-width/2, y-height/2), width, height,
                               color=color, ec=edge_color, linewidth=2.5, zorder=3)
                self.ax.add_patch(rect)
            
            # Node label with IP
            ip_text = self.node_ips.get(node, '')
            label_text = f"{icon} {node}"
            if ip_text:
                label_text += f"\n{ip_text}"
            
            bbox_props = dict(boxstyle='round,pad=0.3', facecolor='white', 
                            edgecolor=edge_color, linewidth=1.5, alpha=0.95)
            self.ax.text(x, y + 0.12, label_text, ha='center', va='center',
                        fontsize=9, fontweight='bold', zorder=4,
                        bbox=bbox_props)

        # Draw packet with trail
        if packet_pos is not None:
            px, py = packet_pos
            
            # Trail effect
            if len(self.packet_trail) > 1:
                trail_x = [p[0] for p in self.packet_trail]
                trail_y = [p[1] for p in self.packet_trail]
                
                for i in range(len(trail_x) - 1):
                    alpha = (i + 1) / len(trail_x) * 0.5
                    self.ax.plot(trail_x[i:i+2], trail_y[i:i+2], 
                               color='#00FF00', linewidth=3, 
                               alpha=alpha, zorder=5)
            
            # Packet visualization
            glow = Circle((px, py), 0.06, color='#00FF00', alpha=0.4, zorder=6)
            self.ax.add_patch(glow)
            
            ring = Circle((px, py), 0.04, color='#00FF00', alpha=0.6, zorder=7)
            self.ax.add_patch(ring)
            
            packet = Circle((px, py), 0.025, color='#00FF00', 
                          ec='#006600', linewidth=2, zorder=8)
            self.ax.add_patch(packet)
            
            self.ax.text(px, py - 0.1, '📦', ha='center', va='center',
                        fontsize=16, zorder=9)

        self.ax.set_aspect('equal')
        self.ax.set_title('Network Topology Visualization', 
                         fontsize=16, fontweight='bold', pad=20)
        self.canvas.draw_idle()

    def on_click(self, event):
        if event.xdata is None or event.ydata is None:
            return
        
        nearest = None
        min_dist = 1e9
        for n, p in self.pos.items():
            dx = p[0] - event.xdata
            dy = p[1] - event.ydata
            d = dx*dx + dy*dy
            if d < min_dist:
                min_dist = d
                nearest = n
        
        if nearest and min_dist < 0.01:
            self.selected_node = nearest
            self.dragging = True
            self.drag_node = nearest
            
            # Update device type selector and IP selector
            self.device_type.set(self.node_devices.get(nearest, 'Router'))
            self.ip_node_var.set(nearest)
            if nearest in self.node_ips:
                self.ip_entry.delete(0, tk.END)
                self.ip_entry.insert(0, self.node_ips[nearest])
        else:
            self.selected_node = None
        
        self.update_comboboxes()
        self.redraw()

    def on_release(self, event):
        self.dragging = False
        self.drag_node = None

    def on_motion(self, event):
        if not self.dragging or event.xdata is None or event.ydata is None:
            return
        if self.drag_node:
            self.pos[self.drag_node] = (event.xdata, event.ydata)
            self.redraw()

    # ---------- Animation with packet loss ----------
    def start_animation(self):
        if self.animating:
            messagebox.showinfo('Animation', 'Animation already running.')
            return
        
        src = self.src_var.get()
        dst = self.dst_var.get()
        
        if not src or not dst:
            messagebox.showwarning('Animate', 'Choose source and destination nodes.')
            return
        
        if src not in self.G.nodes or dst not in self.G.nodes:
            messagebox.showwarning('Animate', 'Source/Destination not in graph.')
            return
        
        # Set packet loss rate
        self.packet_loss_rate = self.loss_var.get() / 100.0
        
        # Check simulation mode
        mode = self.sim_mode.get()
        
        if mode == 'broadcast':
            self.start_broadcast_animation(src, dst)
        else:
            self.start_unicast_animation(src, dst)

    def start_unicast_animation(self, src, dst):
        try:
            path = nx.shortest_path(self.G, source=src, target=dst)
        except nx.NetworkXNoPath:
            messagebox.showerror('Path Error', 'No path between selected nodes.')
            return
        
        self.animating = True
        self.animation_frame = 0
        self.packet_trail = []
        self.current_path = path
        
        src_ip = self.node_ips.get(src, 'N/A')
        dst_ip = self.node_ips.get(dst, 'N/A')
        
        self.log(f"\n{'='*50}")
        self.log(f"🚀 UNICAST TRANSMISSION STARTED")
        self.log(f"Source: {src} ({src_ip})")
        self.log(f"Destination: {dst} ({dst_ip})")
        self.log(f"Path: {' → '.join(path)}")
        self.log(f"Packet Loss Rate: {self.packet_loss_rate*100:.1f}%")
        self.log(f"{'='*50}\n")
        
        self._animate_smooth(path, 0, 0)

    def start_broadcast_animation(self, src, dst):
        # Get all nodes except source
        all_nodes = [n for n in self.G.nodes if n != src]
        
        if not all_nodes:
            messagebox.showinfo('Broadcast', 'No other nodes to broadcast to.')
            return
        
        self.animating = True
        self.animation_frame = 0
        self.packet_trail = []
        self.broadcast_visited = set()
        self.broadcast_rejected = set()
        self.broadcast_accepted = None
        
        src_ip = self.node_ips.get(src, 'N/A')
        dst_ip = self.node_ips.get(dst, 'N/A')
        
        self.log(f"\n{'='*50}")
        self.log(f"📡 BROADCAST TRANSMISSION STARTED")
        self.log(f"Source: {src} ({src_ip})")
        self.log(f"Target IP: {dst_ip}")
        self.log(f"Broadcasting to all {len(all_nodes)} nodes...")
        self.log(f"Packet Loss Rate: {self.packet_loss_rate*100:.1f}%")
        self.log(f"{'='*50}\n")
        
        # Start BFS broadcast
        self._animate_broadcast(src, dst, visited=set([src]))

    def _animate_broadcast(self, current, target, visited):
        if not self.animating:
            return
        
        # Get neighbors not yet visited
        neighbors = [n for n in self.G.neighbors(current) if n not in visited]
        
        if not neighbors:
            # No more neighbors, end broadcast
            self._end_broadcast(target)
            return
        
        # Animate to first neighbor
        neighbor = neighbors[0]
        visited.add(neighbor)
        
        try:
            path = [current, neighbor]
            self._animate_broadcast_segment(path, 0, 0, neighbor, target, visited, neighbors[1:])
        except:
            self._end_broadcast(target)

    def _animate_broadcast_segment(self, path, edge_idx, frame, current_node, 
                                   target, visited, remaining_neighbors):
        if not self.animating:
            return
        
        if edge_idx >= len(path) - 1:
            # Check for packet loss
            if random.random() < self.packet_loss_rate:
                self.log(f"❌ Packet LOST at {current_node}")
                self.broadcast_rejected.add(current_node)
                
                # Continue to remaining neighbors from previous node
                if remaining_neighbors:
                    prev_node = path[0]
                    next_neighbor = remaining_neighbors[0]
                    visited.add(next_neighbor)
                    new_path = [prev_node, next_neighbor]
                    self.root.after(300, lambda: self._animate_broadcast_segment(
                        new_path, 0, 0, next_neighbor, target, visited, remaining_neighbors[1:]))
                else:
                    # Continue broadcast from current node
                    self.root.after(300, lambda: self._animate_broadcast(current_node, target, visited))
                return
            
            # Packet arrived at node
            self.broadcast_visited.add(current_node)
            
            # Check if this node accepts the packet
            current_ip = self.node_ips.get(current_node, '')
            target_ip = self.node_ips.get(target, '')
            
            if current_ip and target_ip and current_ip == target_ip:
                self.log(f"✅ {current_node} ACCEPTED packet (IP match: {current_ip})")
                self.broadcast_accepted = current_node
            else:
                self.log(f"🔄 {current_node} rejected packet (IP: {current_ip} ≠ {target_ip})")
                self.broadcast_rejected.add(current_node)
            
            # Continue to remaining neighbors from previous node
            if remaining_neighbors:
                prev_node = path[0]
                next_neighbor = remaining_neighbors[0]
                visited.add(next_neighbor)
                new_path = [prev_node, next_neighbor]
                self.root.after(300, lambda: self._animate_broadcast_segment(
                    new_path, 0, 0, next_neighbor, target, visited, remaining_neighbors[1:]))
            else:
                # Continue broadcast from current node
                self.root.after(300, lambda: self._animate_broadcast(current_node, target, visited))
            return
        
        # Animate packet movement
        start_node = path[edge_idx]
        end_node = path[edge_idx + 1]
        
        t = frame / self.frames_per_edge
        x1, y1 = self.pos[start_node]
        x2, y2 = self.pos[end_node]
        
        t_eased = self._ease_in_out(t)
        px = x1 + (x2 - x1) * t_eased
        py = y1 + (y2 - y1) * t_eased
        
        self.packet_trail.append((px, py))
        if len(self.packet_trail) > 10:
            self.packet_trail.pop(0)
        
        pulse_nodes = [start_node, end_node]
        
        self.animation_frame += 1
        self.redraw(highlight_path=path, packet_pos=(px, py), 
                   pulse_nodes=pulse_nodes,
                   rejected_nodes=self.broadcast_rejected,
                   broadcast_nodes=[self.broadcast_accepted] if self.broadcast_accepted else None)
        
        if frame < self.frames_per_edge - 1:
            self.root.after(self.animation_speed, 
                          lambda: self._animate_broadcast_segment(
                              path, edge_idx, frame + 1, current_node, 
                              target, visited, remaining_neighbors))
        else:
            self.root.after(self.animation_speed, 
                          lambda: self._animate_broadcast_segment(
                              path, edge_idx + 1, 0, current_node, 
                              target, visited, remaining_neighbors))

    def _end_broadcast(self, target):
        self.animating = False
        self.packet_trail = []
        
        self.log(f"\n{'='*50}")
        if self.broadcast_accepted:
            self.log(f"✅ BROADCAST COMPLETE - Packet accepted by {self.broadcast_accepted}")
        else:
            self.log(f"⚠️ BROADCAST COMPLETE - No node accepted the packet")
        self.log(f"Nodes visited: {len(self.broadcast_visited)}")
        self.log(f"Packets lost: {len(self.broadcast_rejected)}")
        self.log(f"{'='*50}\n")
        
        self.redraw(rejected_nodes=self.broadcast_rejected,
                   broadcast_nodes=[self.broadcast_accepted] if self.broadcast_accepted else None)
        
        # Show summary
        if self.broadcast_accepted:
            messagebox.showinfo('Broadcast Complete', 
                              f'✅ Packet delivered to {self.broadcast_accepted}!\n\n'
                              f'Nodes visited: {len(self.broadcast_visited)}\n'
                              f'Packets lost: {len(self.broadcast_rejected)}')
        else:
            messagebox.showwarning('Broadcast Complete', 
                                  f'⚠️ No node accepted the packet.\n\n'
                                  f'Nodes visited: {len(self.broadcast_visited)}\n'
                                  f'Packets lost: {len(self.broadcast_rejected)}')

    def stop_animation(self):
        self.animating = False
        self.packet_trail = []
        self.redraw()
        self.log("⏹️ Animation stopped by user\n")

    def _animate_smooth(self, path, edge_idx, frame):
        if not self.animating:
            return
        
        if edge_idx >= len(path) - 1:
            # Animation complete - check final delivery
            self.animating = False
            self.packet_trail = []
            
            # Check for packet loss at destination
            if random.random() < self.packet_loss_rate:
                self.log(f"❌ PACKET LOST at destination {path[-1]}")
                self.log(f"{'='*50}\n")
                self.redraw(highlight_path=path)
                messagebox.showerror('Packet Lost!', 
                                   f'❌ Packet was lost at destination!\n\n'
                                   f'Loss occurred at: {path[-1]}\n'
                                   f'Packet loss rate: {self.packet_loss_rate*100:.1f}%')
            else:
                self.log(f"✅ PACKET DELIVERED successfully to {path[-1]}")
                self.log(f"{'='*50}\n")
                self.redraw(highlight_path=path)
                messagebox.showinfo('Success', 
                                  f'✅ Packet delivered successfully to {path[-1]}!')
            return
        
        # Check for packet loss at this hop
        if frame == 0 and edge_idx > 0:
            if random.random() < self.packet_loss_rate:
                current_node = path[edge_idx]
                self.animating = False
                self.packet_trail = []
                
                self.log(f"❌ PACKET LOST at hop {edge_idx}: {current_node}")
                self.log(f"{'='*50}\n")
                
                self.redraw(highlight_path=path[:edge_idx+1])
                messagebox.showerror('Packet Lost!', 
                                   f'❌ Packet was lost during transmission!\n\n'
                                   f'Loss occurred at: {current_node}\n'
                                   f'Hop number: {edge_idx} of {len(path)-1}\n'
                                   f'Packet loss rate: {self.packet_loss_rate*100:.1f}%')
                return
        
        # Current edge
        start_node = path[edge_idx]
        end_node = path[edge_idx + 1]
        
        # Get cable speed multiplier
        cable_type = self.edge_cables.get((start_node, end_node), 'Ethernet')
        speed_mult = CABLE_TYPES[cable_type]['speed']
        adjusted_speed = int(self.animation_speed / speed_mult)
        
        # Interpolate position
        t = frame / self.frames_per_edge
        x1, y1 = self.pos[start_node]
        x2, y2 = self.pos[end_node]
        
        t_eased = self._ease_in_out(t)
        px = x1 + (x2 - x1) * t_eased
        py = y1 + (y2 - y1) * t_eased
        
        # Update trail
        self.packet_trail.append((px, py))
        if len(self.packet_trail) > 15:
            self.packet_trail.pop(0)
        
        pulse_nodes = [start_node, end_node]
        
        # Log progress
        if frame == 0:
            self.log(f"📍 Hop {edge_idx + 1}/{len(path)-1}: {start_node} → {end_node} "
                    f"(via {cable_type})")
        
        self.animation_frame += 1
        self.redraw(highlight_path=path, packet_pos=(px, py), 
                   pulse_nodes=pulse_nodes)
        
        # Next frame
        if frame < self.frames_per_edge - 1:
            self.root.after(adjusted_speed, 
                          lambda: self._animate_smooth(path, edge_idx, frame + 1))
        else:
            self.root.after(adjusted_speed, 
                          lambda: self._animate_smooth(path, edge_idx + 1, 0))

    def _ease_in_out(self, t):
        """Smooth easing function"""
        return t * t * (3.0 - 2.0 * t)

    # ---------- Statistics ----------
    def update_statistics(self):
        self.stats_text.delete(1.0, tk.END)
        
        stats = []
        stats.append("NETWORK STATISTICS")
        stats.append("=" * 40)
        stats.append(f"\nTotal Nodes: {len(self.G.nodes)}")
        stats.append(f"Total Connections: {len(self.G.edges)}")
        
        # Device breakdown
        stats.append("\nDevice Types:")
        device_counts = {}
        for device in self.node_devices.values():
            device_counts[device] = device_counts.get(device, 0) + 1
        for device, count in sorted(device_counts.items()):
            icon = DEVICE_TYPES[device]['icon']
            stats.append(f"  {icon} {device}: {count}")
        
        # Cable breakdown
        stats.append("\nCable Types:")
        cable_counts = {}
        for cable in self.edge_cables.values():
            cable_counts[cable] = cable_counts.get(cable, 0) + 1
        for cable, count in sorted(cable_counts.items()):
            stats.append(f"  {cable}: {count}")
        
        # IP assignments
        stats.append(f"\nIP Addresses Assigned: {len(self.node_ips)}")
        stats.append(f"Unassigned Nodes: {len(self.G.nodes) - len(self.node_ips)}")
        
        # Network metrics
        if len(self.G) > 0:
            stats.append("\nNetwork Metrics:")
            stats.append(f"  Connected: {'Yes' if nx.is_connected(self.G) else 'No'}")
            if nx.is_connected(self.G):
                stats.append(f"  Diameter: {nx.diameter(self.G)}")
                stats.append(f"  Avg Path Length: {nx.average_shortest_path_length(self.G):.2f}")
            stats.append(f"  Density: {nx.density(self.G):.3f}")
        
        self.stats_text.insert(1.0, '\n'.join(stats))

    # ---------- Save/Load ----------
    def save_topology(self):
        fname = filedialog.asksaveasfilename(
            defaultextension='.json',
            filetypes=[('JSON files', '*.json'), ('All files', '*.*')])
        if not fname:
            return
        
        data = {
            'nodes': list(self.G.nodes),
            'edges': list(self.G.edges),
            'pos': {n: list(self.pos[n]) for n in self.pos},
            'devices': self.node_devices,
            'ips': self.node_ips,
            'cables': {f"{a},{b}": cable for (a,b), cable in self.edge_cables.items()}
        }
        
        with open(fname, 'w') as f:
            json.dump(data, f, indent=2)
        
        self.log(f"💾 Topology saved to: {fname}")
        messagebox.showinfo('Success', f'✅ Topology saved to:\n{fname}')

    def load_topology(self):
        fname = filedialog.askopenfilename(
            filetypes=[('JSON files', '*.json'), ('All files', '*.*')])
        if not fname:
            return
        
        try:
            with open(fname, 'r') as f:
                data = json.load(f)
            
            self.G.clear()
            for n in data.get('nodes', []):
                self.G.add_node(n)
            for a, b in data.get('edges', []):
                self.G.add_edge(a, b)
            
            pos_data = data.get('pos', {})
            self.pos = {n: tuple(pos_data.get(n, (0.0, 0.0))) 
                       for n in self.G.nodes}
            
            self.node_devices = data.get('devices', {})
            self.node_ips = data.get('ips', {})
            
            # Load cable types
            self.edge_cables = {}
            cables_data = data.get('cables', {})
            for edge_str, cable in cables_data.items():
                a, b = edge_str.split(',')
                self.edge_cables[(a, b)] = cable
            
            # Update node count
            maxk = 0
            for n in self.G.nodes:
                if n.startswith('N'):
                    try:
                        k = int(n[1:])
                        if k > maxk:
                            maxk = k
                    except:
                        pass
            self.node_count = max(self.node_count, maxk)
            
            self.update_comboboxes()
            self.update_ip_display()
            self.redraw()
            
            self.log(f"📂 Topology loaded from: {fname}")
            messagebox.showinfo('Success', f'✅ Topology loaded from:\n{fname}')
        
        except Exception as e:
            messagebox.showerror('Error', f'Failed to load topology:\n{str(e)}')


# ---------- Run ----------
if __name__ == '__main__':
    root = tk.Tk()
    app = NetworkVisualizerApp(root)
    root.mainloop()
