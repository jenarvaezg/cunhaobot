import random

thumbs = [
    "https://cdn.20m.es/img2/recortes/2018/02/06/632781-600-338.jpg",
    "https://i.blogs.es/c60c05/quien-javier/450_1000.jpg",
    "https://media-cdn.tripadvisor.com/media/photo-s/0f/f9/86/eb/junto-a-mi-cunado-compartiendo.jpg",
    "https://fotos.perfil.com/2016/10/26/1026claudiominnicellig.jpg",
    "https://www.ecestaticos.com/imagestatic/clipping/7f5/900/7f59009441d3cf042f374f50756f3c5b/tu-cunado-ese-que-dice-que-escribe.jpg?mtime=1456847457",
    "https://i.ytimg.com/vi/NyOwsYAPzTE/hqdefault.jpg",
    "https://pbs.twimg.com/media/DFRYYkRXgAIGOjI.jpg",
    "http://www.eluniversalqueretaro.mx/sites/default/files/styles/f03-651x400/public/2018/04/06/q8-20.jpg.jpg?itok=G2zZUM1c",
    "https://static3.elcomercio.es/www/pre2017/multimedia/noticias/201703/26/media/22940314.jpg",
    "https://www.elplural.com/uploads/s1/62/50/39/el-lider-de-vox-santiago-abascal-sin-barba_6_585x329.png",
    "https://pbs.twimg.com/media/DwA6mRuW0AAj8FX.jpg",
    "https://amenzing.com/wp-content/uploads/2018/12/santiago-abascal.jpg",
    "https://images.uncyclomedia.co/inciclopedia/es/1/14/Cu%C3%B1ado.png",
    "https://img.asmedia.epimg.net/resizer/v2/REG5OGLOHNPPBLDIFINBZF4TVQ.jpg?auth=b4ca2f2a1999954ce7007d7afadcb41b5d2d718cad5746ce07e354a6b0f3153c&width=1472&height=1104&smart=true",
]


def get_thumb() -> str:
    return random.choice(thumbs)


def apelativo() -> str:
    from services import phrase_service

    return phrase_service.get_random(long=False).text
