import sectionproperties.pre.sections as sections
from sectionproperties.analysis.cross_section import CrossSection

#Class to define SHS Object and allow operations such as analyse geometry
class custom_hs:
    def __init__(self,d,t):
        self.d = d
        self.t = t

    def rhs(self,b):
        geometry = sections.Rhs(d=self.d, b=b, t=self.t, r_out=self.t*2.0, n_r=3)
        mesh = geometry.create_mesh(mesh_sizes=[self.t**2])
        self.section = CrossSection(geometry, mesh)
        return self.section.calculate_frame_properties()

    def chs(self):
        geometry = sections.Chs(d=self.d,t=self.t,n=70)
        mesh = geometry.create_mesh(mesh_sizes=[self.t**2])
        self.section = CrossSection(geometry, mesh)
        return self.section.calculate_frame_properties()

    def visualise(self):
        fig, ax = self.section.plot_centroids()
        return fig, ax