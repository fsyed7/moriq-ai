// Short architecture facts for browsing. General knowledge written by AI, not MORIQ sources; the card says so.
export const FACTS = [
  {about: 'the Pantheon', text: 'The Pantheon in Rome, finished around 126 AD, still has the world\'s largest unreinforced concrete dome, about 43 metres across.'},
  {about: 'Roman concrete', text: 'Roman marine concrete grows stronger over time, because seawater reacts with the volcanic ash in its mix.'},
  {about: 'the Great Pyramid', text: 'The Great Pyramid of Giza was the tallest structure on Earth for about 3,800 years.'},
  {about: 'the Hagia Sophia', text: 'The first dome of the Hagia Sophia, completed in 537, partly collapsed in 558 after earthquakes and had to be rebuilt.'},
  {about: 'Fallingwater', text: 'Frank Lloyd Wright built Fallingwater over a waterfall in the 1930s. The clients had expected a house with a view of the falls.'},
  {about: 'the Sagrada Família', text: 'Construction of the Sagrada Família began in 1882. Antoni Gaudí took over in 1883 and died in 1926 with it far from finished.'},
  {about: 'the Sydney Opera House', text: 'Jørn Utzon resigned from the Sydney Opera House in 1966 and never saw his finished building in person.'},
  {about: 'the Guggenheim Bilbao', text: 'Frank Gehry\'s office used CATIA, software developed for aircraft design, to make the Guggenheim Bilbao\'s curves buildable.'},
  {about: 'the Crystal Palace', text: 'Joseph Paxton\'s Crystal Palace of 1851 used standardised iron and glass parts, an early landmark of prefabrication.'},
  {about: 'the Centre Pompidou', text: 'The Centre Pompidou wears its services outside, with colour-coded pipes: blue for air, green for water and yellow for electricity.'},
  {about: 'Villa Savoye', text: 'Le Corbusier\'s Villa Savoye demonstrates his five points: pilotis, roof garden, free plan, ribbon windows and free façade.'},
  {about: 'the Eiffel Tower', text: 'The Eiffel Tower can grow by several centimetres in summer as its iron expands in the heat.'},
  {about: 'the Burj Khalifa', text: 'The Burj Khalifa in Dubai stands 828 metres tall. Its Y-shaped plan helps it resist strong winds.'},
  {about: 'Zaha Hadid', text: 'In 2004, Zaha Hadid became the first woman to win the Pritzker Architecture Prize.'},
  {about: 'Balkrishna Doshi', text: 'In 2018, Balkrishna Doshi became the first Indian architect to win the Pritzker Prize. He had worked with Le Corbusier in Paris and India.'},
  {about: 'Tadao Ando', text: 'Tadao Ando had no formal architectural training and once worked as a boxer. He went on to win the Pritzker Prize in 1995.'},
  {about: 'Oscar Niemeyer', text: 'Oscar Niemeyer designed the main civic buildings of Brasília and kept working until shortly before his death at 104.'},
  {about: 'Geoffrey Bawa', text: 'Geoffrey Bawa trained as a lawyer and qualified as an architect in his late thirties, then became a leading voice of tropical modernism.'},
  {about: 'Laurie Baker', text: 'Laurie Baker built low-cost homes in Kerala using the rat-trap bond, a brick wall with hollow cavities that saves material and insulates.'},
  {about: 'Charles Correa', text: 'Charles Correa\'s Kanchanjunga Apartments in Mumbai give each home a double-height garden terrace in place of a conventional balcony.'},
  {about: 'Louis Kahn', text: 'Louis Kahn designed both the Indian Institute of Management in Ahmedabad and Bangladesh\'s National Assembly in Dhaka.'},
  {about: 'Chandigarh', text: 'Le Corbusier led the master plan of Chandigarh in the 1950s, one of the best-known planned cities of the twentieth century.'},
  {about: 'the Lotus Temple', text: 'The Lotus Temple in Delhi, designed by Fariborz Sahba, is formed from 27 free-standing petals clad in marble.'},
  {about: 'the Charminar', text: 'Hyderabad\'s Charminar, built in 1591, has four minarets rising from the corners of a great square arch.'},
  {about: 'Golconda Fort', text: 'Golconda Fort near Hyderabad is famous for its acoustics: a handclap at the entrance is said to carry up to the hilltop citadel.'},
  {about: 'Gol Gumbaz', text: 'The whispering gallery of Gol Gumbaz in Bijapur carries even a quiet whisper around its enormous dome.'},
  {about: 'stepwells', text: 'Rani ki Vav in Gujarat, a stepwell lined with hundreds of carved sculptures, became a UNESCO World Heritage Site in 2014.'},
  {about: 'jali screens', text: 'Jali screens filter harsh sun, keep privacy and speed up passing air, a climate device that has been used across India for centuries.'},
  {about: 'wind towers', text: 'Traditional wind towers across the Gulf, known as barjeel, catch breezes above the roofline and draw them down to cool the rooms below.'},
  {about: 'the Bahrain World Trade Center', text: 'The Bahrain World Trade Center, finished in 2008, has three large wind turbines mounted on bridges between its two towers.'},
];

export function shuffled(items = FACTS) {
  const copy = [...items];
  for (let i = copy.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [copy[i], copy[j]] = [copy[j], copy[i]];
  }
  return copy;
}

export function askAbout(fact) {
  return `What can architects learn from ${fact.about}?`;
}
