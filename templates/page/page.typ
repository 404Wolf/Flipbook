#set page(
  width: eval(sys.inputs.width),
  height: eval(sys.inputs.height), 
  margin: eval(sys.inputs.margin),
)

#place(
  top + left,
  image(sys.inputs.imageSrc, height: 102%, width: 102%),
  clearance: 0in,
)

#let timestamp = [
  #text(sys.inputs.timestamp, fill: color.white, font: "0xProto Nerd Font", size: 0.07in)
]
#place(bottom + right, pad(0.025in, timestamp))
