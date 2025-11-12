import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import networkx as nx
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyBboxPatch
from matplotlib.collections import LineCollection
import json
import numpy as np
from matplotlib.colors import LinearSegmentedColormap

# ---------- Helper functions ----------

def default_node_label(n):
    return f"N{n}"

# ---------- Main App ----------
class NetworkVisualizerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Network Topology Visualizer - Enhanced Edition")
        
        # Get screen dimensions for optimal sizing
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        
        # Set window size to 80% of screen
        window_width = int(screen_width * 0.8)
        window_height = int(screen_height * 0.8)
        self.root.geometry(f"{window_width}x{window_height}")
        
        self.G = nx.Graph()
        self.pos = {}
        self.node_count = 0
        self.selected_node = None
        self.dragging = False
        self.animating = False
        self.animation_frame = 0
        self.packet_trail = []
        
        # Animation parameters
        self.animation_speed = 100  # ms per frame
        self.frames_per_edge = 20  # frames to traverse one edge
        
        # Create main container with grid
        main_container = ttk.Frame(root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        main_container.grid_columnconfigure(0, weight=1)
        main_container.grid_rowconfigure(0, weight=1)
        
        # Matplotlib figure - much larger
        fig_width = max(12, window_width // 100)
        fig_height = max(9, window_height // 100)
        self.fig, self.ax = plt.subplots(figsize=(fig_width, fig_height))
        self.fig.patch.set_facecolor('#f0f0f0')
        self.ax.set_facecolor('#ffffff')
        plt.tight_layout()
        
        # Canvas with better sizing
        canvas_frame = ttk.Frame(main_container)
        canvas_frame.grid(row=0, column=0, sticky='nsew', padx=(0, 10))
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=canvas_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.canvas.mpl_connect('button_press_event', self.on_click)
        self.canvas.mpl_connect('button_release_event', self.on_release)
        self.canvas.mpl_connect('motion_notify_event', self.on_motion)

        # Enhanced control panel
        ctrlframe = ttk.Frame(main_container, padding=10)
        ctrlframe.grid(row=0, column=1, sticky='nsew')
        
        # Style configuration
        style = ttk.Style()
        style.configure('Title.TLabel', font=('Segoe UI', 14, 'bold'))
        style.configure('Section.TLabel', font=('Segoe UI', 11, 'bold'))
        style.configure('TButton', padding=8, font=('Segoe UI', 10))

        # Title
        ttk.Label(ctrlframe, text='🌐 Network Control Panel', 
                 style='Title.TLabel').grid(row=0, column=0, columnspan=2, pady=(0,15))

        # Topology section
        ttk.Label(ctrlframe, text='Topology Controls', 
                 style='Section.TLabel').grid(row=1, column=0, columnspan=2, pady=(0,8))
        
        ttk.Button(ctrlframe, text='➕ Add Node', command=self.add_node).grid(
            row=2, column=0, sticky='ew', padx=(0,5), pady=3)
        ttk.Button(ctrlframe, text='➖ Remove Node', command=self.remove_selected_node).grid(
            row=2, column=1, sticky='ew', pady=3)

        ttk.Separator(ctrlframe, orient='horizontal').grid(
            row=3, column=0, columnspan=2, sticky='ew', pady=10)

        # Edge controls
        ttk.Label(ctrlframe, text='Edge Management', 
                 style='Section.TLabel').grid(row=4, column=0, columnspan=2, pady=(0,8))
        
        ttk.Label(ctrlframe, text='From Node:').grid(row=5, column=0, sticky='w', pady=2)
        ttk.Label(ctrlframe, text='To Node:').grid(row=5, column=1, sticky='w', pady=2)
        
        self.edge_a = tk.StringVar()
        self.edge_b = tk.StringVar()
        self.edge_a_cb = ttk.Combobox(ctrlframe, textvariable=self.edge_a, 
                                       state='readonly', width=12, font=('Segoe UI', 10))
        self.edge_b_cb = ttk.Combobox(ctrlframe, textvariable=self.edge_b, 
                                       state='readonly', width=12, font=('Segoe UI', 10))
        self.edge_a_cb.grid(row=6, column=0, pady=3)
        self.edge_b_cb.grid(row=6, column=1, pady=3)
        
        ttk.Button(ctrlframe, text='🔗 Add Edge', command=self.add_edge).grid(
            row=7, column=0, sticky='ew', padx=(0,5), pady=3)
        ttk.Button(ctrlframe, text='✂️ Remove Edge', command=self.remove_edge).grid(
            row=7, column=1, sticky='ew', pady=3)

        ttk.Separator(ctrlframe, orient='horizontal').grid(
            row=8, column=0, columnspan=2, sticky='ew', pady=10)

        # Simulation section
        ttk.Label(ctrlframe, text='Packet Simulation', 
                 style='Section.TLabel').grid(row=9, column=0, columnspan=2, pady=(0,8))
        
        ttk.Label(ctrlframe, text='Source:').grid(row=10, column=0, sticky='w', pady=2)
        ttk.Label(ctrlframe, text='Destination:').grid(row=10, column=1, sticky='w', pady=2)
        
        self.src_var = tk.StringVar()
        self.dst_var = tk.StringVar()
        self.src_cb = ttk.Combobox(ctrlframe, textvariable=self.src_var, 
                                    state='readonly', width=12, font=('Segoe UI', 10))
        self.dst_cb = ttk.Combobox(ctrlframe, textvariable=self.dst_var, 
                                    state='readonly', width=12, font=('Segoe UI', 10))
        self.src_cb.grid(row=11, column=0, pady=3)
        self.dst_cb.grid(row=11, column=1, pady=3)
        
        ttk.Button(ctrlframe, text='🚀 Animate Packet Flow', 
                  command=self.start_animation).grid(
            row=12, column=0, columnspan=2, sticky='ew', pady=(5,3))
        
        ttk.Button(ctrlframe, text='⏹️ Stop Animation', 
                  command=self.stop_animation).grid(
            row=13, column=0, columnspan=2, sticky='ew', pady=3)

        ttk.Separator(ctrlframe, orient='horizontal').grid(
            row=14, column=0, columnspan=2, sticky='ew', pady=10)

        # File operations
        ttk.Label(ctrlframe, text='File Operations', 
                 style='Section.TLabel').grid(row=15, column=0, columnspan=2, pady=(0,8))
        
        ttk.Button(ctrlframe, text='💾 Save Topology', command=self.save_topology).grid(
            row=16, column=0, sticky='ew', padx=(0,5), pady=3)
        ttk.Button(ctrlframe, text='📂 Load Topology', command=self.load_topology).grid(
            row=16, column=1, sticky='ew', pady=3)

        ttk.Separator(ctrlframe, orient='horizontal').grid(
            row=17, column=0, columnspan=2, sticky='ew', pady=10)

        # Tips section
        tips_frame = ttk.LabelFrame(ctrlframe, text='💡 Tips', padding=10)
        tips_frame.grid(row=18, column=0, columnspan=2, sticky='ew', pady=(0,10))
        
        tips_text = (
            "• Click nodes to select\n"
            "• Drag nodes to reposition\n"
            "• Watch animated packet flows\n"
            "• Save/load network topologies"
        )
        ttk.Label(tips_frame, text=tips_text, justify=tk.LEFT, 
                 font=('Segoe UI', 9)).pack(anchor='w')

        # Initial draw
        self.redraw()

    # ---------- Topology editing ----------
    def add_node(self):
        self.node_count += 1
        nid = default_node_label(self.node_count)
        self.G.add_node(nid)
        
        # Better initial positioning in a circular layout
        angle = 2 * np.pi * len(self.pos) / max(8, len(self.pos) + 1)
        radius = 0.5
        self.pos[nid] = (radius * np.cos(angle), radius * np.sin(angle))
        
        self.update_comboboxes()
        self.redraw()

    def remove_selected_node(self):
        if self.selected_node and self.selected_node in self.G.nodes:
            self.G.remove_node(self.selected_node)
            self.pos.pop(self.selected_node, None)
            self.selected_node = None
            self.update_comboboxes()
            self.redraw()
        else:
            messagebox.showinfo('Remove Node', 
                              'Select a node on the canvas (click) to remove it.')

    def add_edge(self):
        a = self.edge_a.get()
        b = self.edge_b.get()
        if not a or not b:
            messagebox.showwarning('Add Edge', 'Choose two nodes.')
            return
        if a == b:
            messagebox.showwarning('Add Edge', 'Choose two different nodes.')
            return
        self.G.add_edge(a, b)
        self.redraw()

    def remove_edge(self):
        a = self.edge_a.get()
        b = self.edge_b.get()
        if not a or not b:
            messagebox.showwarning('Remove Edge', 'Choose two nodes.')
            return
        if self.G.has_edge(a, b):
            self.G.remove_edge(a, b)
            self.redraw()
        else:
            messagebox.showinfo('Remove Edge', 'Edge does not exist.')

    def update_comboboxes(self):
        nodes = sorted(list(self.G.nodes))
        for cb in (self.edge_a_cb, self.edge_b_cb, self.src_cb, self.dst_cb):
            cb['values'] = nodes
            val = cb.get()
            if val not in nodes:
                cb.set('')

    # ---------- Enhanced Drawing ----------
    def redraw(self, highlight_path=None, packet_pos=None, pulse_nodes=None):
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

        # Draw edges with enhanced styling
        edge_colors = []
        edge_widths = []
        edge_styles = []
        
        for edge in self.G.edges:
            if highlight_path and len(highlight_path) >= 2:
                path_edges = list(zip(highlight_path, highlight_path[1:]))
                if edge in path_edges or (edge[1], edge[0]) in path_edges:
                    edge_colors.append('#ff4444')
                    edge_widths.append(4.0)
                    edge_styles.append('solid')
                else:
                    edge_colors.append('#cccccc')
                    edge_widths.append(2.0)
                    edge_styles.append('solid')
            else:
                edge_colors.append('#999999')
                edge_widths.append(2.5)
                edge_styles.append('solid')

        # Draw edges
        for i, edge in enumerate(self.G.edges):
            x = [self.pos[edge[0]][0], self.pos[edge[1]][0]]
            y = [self.pos[edge[0]][1], self.pos[edge[1]][1]]
            self.ax.plot(x, y, color=edge_colors[i], linewidth=edge_widths[i],
                        linestyle=edge_styles[i], zorder=1, alpha=0.6)

        # Draw nodes with enhanced styling
        for node in self.G.nodes:
            x, y = self.pos[node]
            
            # Calculate base size and color
            base_size = 800
            color = '#4A90E2'
            edge_color = '#2E5C8A'
            
            if node == self.selected_node:
                color = '#FF9500'
                edge_color = '#CC7700'
                base_size = 900
            
            # Pulse effect for active nodes
            pulse_factor = 1.0
            if pulse_nodes and node in pulse_nodes:
                pulse_factor = 1.0 + 0.3 * np.sin(self.animation_frame * 0.3)
                
                # Glow effect
                glow = Circle((x, y), 0.08 * pulse_factor, 
                            color=color, alpha=0.3, zorder=2)
                self.ax.add_patch(glow)
            
            # Main node
            circle = Circle((x, y), 0.05 * pulse_factor, 
                          color=color, ec=edge_color, linewidth=2.5, zorder=3)
            self.ax.add_patch(circle)
            
            # Node label with background
            bbox_props = dict(boxstyle='round,pad=0.3', facecolor='white', 
                            edgecolor=edge_color, linewidth=1.5, alpha=0.9)
            self.ax.text(x, y, node, ha='center', va='center',
                        fontsize=11, fontweight='bold', zorder=4,
                        bbox=bbox_props)

        # Draw packet with trail effect
        if packet_pos is not None:
            px, py = packet_pos
            
            # Draw trail
            if len(self.packet_trail) > 1:
                trail_x = [p[0] for p in self.packet_trail]
                trail_y = [p[1] for p in self.packet_trail]
                
                # Create gradient effect for trail
                for i in range(len(trail_x) - 1):
                    alpha = (i + 1) / len(trail_x) * 0.5
                    self.ax.plot(trail_x[i:i+2], trail_y[i:i+2], 
                               color='#00FF00', linewidth=3, 
                               alpha=alpha, zorder=5)
            
            # Outer glow
            glow = Circle((px, py), 0.06, color='#00FF00', alpha=0.4, zorder=6)
            self.ax.add_patch(glow)
            
            # Middle ring
            ring = Circle((px, py), 0.04, color='#00FF00', alpha=0.6, zorder=7)
            self.ax.add_patch(ring)
            
            # Packet core
            packet = Circle((px, py), 0.025, color='#00FF00', 
                          ec='#006600', linewidth=2, zorder=8)
            self.ax.add_patch(packet)
            
            # Packet label
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

    # ---------- Enhanced Animation ----------
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
        
        try:
            path = nx.shortest_path(self.G, source=src, target=dst)
        except nx.NetworkXNoPath:
            messagebox.showerror('Path Error', 'No path between selected nodes.')
            return
        
        self.animating = True
        self.animation_frame = 0
        self.packet_trail = []
        self.current_path = path
        self._animate_smooth(path, 0, 0)

    def stop_animation(self):
        self.animating = False
        self.packet_trail = []
        self.redraw()

    def _animate_smooth(self, path, edge_idx, frame):
        if not self.animating:
            return
        
        if edge_idx >= len(path) - 1:
            # Animation complete
            self.animating = False
            self.packet_trail = []
            self.redraw(highlight_path=path)
            messagebox.showinfo('Success', '✅ Packet delivered successfully!')
            return
        
        # Current edge
        start_node = path[edge_idx]
        end_node = path[edge_idx + 1]
        
        # Interpolate position
        t = frame / self.frames_per_edge
        x1, y1 = self.pos[start_node]
        x2, y2 = self.pos[end_node]
        
        # Smooth easing function
        t_eased = self._ease_in_out(t)
        px = x1 + (x2 - x1) * t_eased
        py = y1 + (y2 - y1) * t_eased
        
        # Update trail
        self.packet_trail.append((px, py))
        if len(self.packet_trail) > 15:
            self.packet_trail.pop(0)
        
        # Determine pulsing nodes
        pulse_nodes = [start_node, end_node]
        
        # Redraw
        self.animation_frame += 1
        self.redraw(highlight_path=path, packet_pos=(px, py), 
                   pulse_nodes=pulse_nodes)
        
        # Next frame
        if frame < self.frames_per_edge - 1:
            self.root.after(self.animation_speed, 
                          lambda: self._animate_smooth(path, edge_idx, frame + 1))
        else:
            self.root.after(self.animation_speed, 
                          lambda: self._animate_smooth(path, edge_idx + 1, 0))

    def _ease_in_out(self, t):
        """Smooth easing function for animation"""
        return t * t * (3.0 - 2.0 * t)

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
            'pos': {n: list(self.pos[n]) for n in self.pos}
        }
        
        with open(fname, 'w') as f:
            json.dump(data, f, indent=2)
        
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
            self.redraw()
            messagebox.showinfo('Success', f'✅ Topology loaded from:\n{fname}')
        
        except Exception as e:
            messagebox.showerror('Error', f'Failed to load topology:\n{str(e)}')


# ---------- Run ----------
if __name__ == '__main__':
    root = tk.Tk()
    app = NetworkVisualizerApp(root)
    root.mainloop()