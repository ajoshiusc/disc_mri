
"""
mesh2=patch_color_attrib(atlas_left, values=atlas_left.vertices[:,1], cmap='jet', clim=[0,70])


fig = go.Figure(data=[go.Mesh3d(
    x=mesh2.vertices[:, 0],
    y=mesh2.vertices[:,1],
    z=mesh2.vertices[:,2],
    i=mesh2.faces[:, 0],
    j=mesh2.faces[:,1],
    k=mesh2.faces[:,2],
    vertexcolor=mesh2.vColor, lighting=dict(ambient=0.5,roughness=0.5,diffuse=0.5,specular=0.5))])
fig.update_layout(autosize=True,scene=dict(aspectmode="data", camera=dict(up=dict(x=0, y=1., z=0),eye=dict(x=0, y=0, z=2)),xaxis=dict(visible=False,showgrid= False,zeroline= False),
              yaxis=dict(visible=False,showgrid= False,zeroline= False), zaxis=dict(visible=False,showgrid= False,zeroline= False)))
#fig.update_layout(xaxis_showgrid=False, yaxis_showgrid=False)
fig.update_yaxes(automargin=True)
fig.update_xaxes(automargin=True)
fig.layout.scene.camera.projection.type = "orthographic"

fig.update_layout(
    margin=dict(l=0, r=0, t=0, b=0),
)
# Save the plot to a PNG file
png_file_path = 'output_plotly.png'
# Show the plot

pio.write_image(fig, png_file_path)
pio.show(fig)
"""