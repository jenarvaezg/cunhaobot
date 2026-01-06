// SESIÓN DJ CUÑAO: "Pata Negra Edition" - VERSIÓN ESTABLE
// Solo usamos métodos garantizados: gain, room, delay, lpf, shape.

samples({
  cunao: 'https://raw.githubusercontent.com/TiTo-S/skypelive_sounds/master/sounds/cu%C3%B1ao.wav',
  risa: 'https://raw.githubusercontent.com/F-S-C/vlc-soundboard/master/sounds/Risitas.mp3',
  esoesasi: 'https://raw.githubusercontent.com/TiTo-S/skypelive_sounds/master/sounds/eso-es-asi.wav'
});

setcps(128/60)

const intro = stack(
  s("bd*4").gain(1.2).room(0.2),
  s("hh*8").gain(0.6),
  s("esoesasi").gain(0.9).room(0.4).delay(0.5)
);

const estribillo = stack(
  s("bd*4").gain(1.2),
  s("~ sn").gain(1).room(0.5).delay(0.25),
  s("hh*16").gain(0.6),
  note("c2 [c2 g1] f1 [g1 g#1]").s("saw").gain(0.7).lpf(1200),
  note("c4 g4 f4 e4").s("superhex").gain(0.5).room(0.5).delay(0.5),
  s("cunao").gain(0.6)
);

const breakdown = stack(
  s("risa").gain(0.7).room(0.6).delay(0.5),
  note("c4 g4 f4 e4").s("superhex").gain(0.4).room(0.7).lpf(sine.slow(4).range(400, 2000))
);

const subida = stack(
  s("sn*16").gain(line(0.2, 1.2)),
  note("c4*8").s("superhex").gain(0.5).lpf(line(1000, 5000)),
  s("risa").gain(0.6).speed(line(1, 1.5))
);

const drop = stack(
  s("bd*4").gain(1.2),
  s("~ sn").gain(1.2).room(0.3),
  s("hh*16").gain(0.6),
  note("c2 [c2 g1] f1 [g1 g#1]").s("saw").gain(1.2),
  note("c5 g4 f4 e4").s("superhex").gain(0.6).room(0.4).delay(0.25),
  s("cunao").gain(1.5)
);

cat(
  intro, intro,
  estribillo, estribillo,
  breakdown,
  subida,
  drop, drop, drop, drop,
  s("esoesasi").gain(1.2).room(0.5)
)
