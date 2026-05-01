"""Download and resize Sport Global logos to 256x256 PNG thumbnails."""

import io
import urllib.request
from pathlib import Path
from PIL import Image

LOGOS_DIR = Path(__file__).parent.parent / "custom_components" / "israel_tv" / "logos"
TARGET_SIZE = (256, 256)
BG_COLOR = (15, 25, 35)  # dark navy, matches HA dark theme

CHANNELS = [
    ("sg_30a_golf_kingdom", "https://golfkingdom.net/wp-content/uploads/2022/04/golf-kingdom-st.jpg"),
    ("sg_accdn", "https://i.imgur.com/V6Kaqha.png"),
    ("sg_aci_sport_tv", "https://i.imgur.com/U8cHMOt.png"),
    ("sg_ado_tv", "https://i.imgur.com/pxFamLr.png"),
    ("sg_africa_24_sport", "https://i0.wp.com/africa24tv.com/wp-content/uploads/2023/12/LOGO-AFRICASPORT-4-HD-sans-fond.png?fit=512%2C107&ssl=1"),
    ("sg_alkass_one", "https://i.imgur.com/10mmlha.png"),
    ("sg_alkass_two", "https://i.imgur.com/8w61kFX.png"),
    ("sg_alkass_three", "https://i.imgur.com/d57BdFh.png"),
    ("sg_alkass_four", "https://i.imgur.com/iDL65Wu.png"),
    ("sg_alkass_five", "https://i.imgur.com/6RGNGsM.png"),
    ("sg_alkass_six", "https://i.imgur.com/CrPSPSC.png"),
    ("sg_alkass_seven", "https://i.imgur.com/3eyHP3S.png"),
    ("sg_alkass_shoof", "https://shoof.alkass.net/assets/images/shoof.png"),
    ("sg_alkass_shoof_2", "https://shoof.alkass.net/assets/images/shoof2.png"),
    ("sg_as3_sport_tv", "https://i.ibb.co/bRmGbsyV/A3-SPORTTV.jpg"),
    ("sg_atg_live", "https://i.imgur.com/bPWFXkL.png"),
    ("sg_bahrain_sports_1", "https://i.imgur.com/fBpLsbC.png"),
    ("sg_bahrain_sports_2", "https://i.imgur.com/ZkuZmIo.png"),
    ("sg_bein_sports_xtra_es", "https://i.imgur.com/V562tpO.png"),
    ("sg_bek_tv_sports_west", "https://i.imgur.com/1l3t5jd.png"),
    ("sg_bellator_mma", "https://i.imgur.com/VBKoLHk.png"),
    ("sg_cazetv", "https://upload.wikimedia.org/wikipedia/en/thumb/6/64/Caz%C3%A9TV_logo.svg/1280px-Caz%C3%A9TV_logo.svg.png"),
    ("sg_cctv_16", "https://i.imgur.com/ZzV6JQp.png"),
    ("sg_cdn_deportes", "https://i.imgur.com/yU5LqTL.png"),
    ("sg_colimdot_tv", "https://i.imgur.com/ZeUgLCa.png"),
    ("sg_cricket_gold", "https://resources.cricket-australia.pulselive.com/cricket-australia/photo/2025/07/25/836eddae-4329-4542-ad17-dcd37e9d951a/Cricket-Gold-1920x1080_noBG.png"),
    ("sg_ct_sport", "https://upload.wikimedia.org/wikipedia/commons/thumb/7/72/%C4%8CT_sport_logo.png/960px-%C4%8CT_sport_logo.png"),
    ("sg_dazn_combat", "https://i.postimg.cc/VsW3Jsrz/logo-DAZN-Combat.png"),
    ("sg_dd_sports_sd", "https://dtil.tmsimg.com/assets/s158255_ld_h15_aa.png?lock=720x540"),
    ("sg_deportes_tvc", "https://i.imgur.com/Y1t8xkL.png"),
    ("sg_dong_nai_2", "https://i.imgur.com/tNKPSkO.png"),
    ("sg_draftkings_network", "https://i.imgur.com/SFYhgrt.png"),
    ("sg_equidia", "https://i.imgur.com/QPpbRcZ.png"),
    ("sg_ert_sports_1", "https://i.imgur.com/EsczO2H.png"),
    ("sg_ert_sports_2", "https://i.imgur.com/b2SNQPi.png"),
    ("sg_espn8_the_ocho", "https://images.fubo.tv/channel-config-ui/station-logos/on-dark/espn_8_the_ocho_bw.png"),
    ("sg_esport3", "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9a/Esport3.svg/960px-Esport3.svg.png"),
    ("sg_fanduel_racing", "https://i.imgur.com/84lMjSj.png"),
    ("sg_fanduel_tv", "https://i.imgur.com/YPHrFU0.png"),
    ("sg_fb_tv", "https://i.imgur.com/qBVqtYd.png"),
    ("sg_floracing_247", "https://a.jsrdn.com/hls/22883/floracing-247/logo_20231219_225054_24.png"),
    ("sg_fox_sports", "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0c/FOX_Sports_logo.svg/960px-FOX_Sports_logo.svg.png"),
    ("sg_fox_sports_es", "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3b/FOX_Deportes_logo.png/960px-FOX_Deportes_logo.png"),
    ("sg_ftf_sports", "https://i.imgur.com/yvUjOI3.png"),
    ("sg_ftv", "https://i.imgur.com/YOr1Oac.png"),
    ("sg_fubo_sports", "https://i.imgur.com/qFNRJLb.png"),
    ("sg_fuel_tv", "https://i.imgur.com/I8mviBy.png"),
    ("sg_fuel_tv_emea", "https://i.imgur.com/I8mviBy.png"),
    ("sg_futbol", "https://i.imgur.com/RngmCDn.png"),
    ("sg_game_plus", "https://i.imgur.com/Lj69WbR.png"),
    ("sg_gem_fit", "https://i.imgur.com/7FQxaII.png"),
    ("sg_goal_zone", "https://shahid.mbc.net/mediaObject/18bf9987-49ab-4c51-bb94-c568efa51db7?height=auto&width=512&croppingPoint=&version=1&type=png"),
    ("sg_gol_classics", "https://golstadium.com/_next/image?url=%2Fimg%2Fhome%2Fchannels%2Fthumb-gol-classics.jpg&w=1920&q=75"),
    ("sg_golf_channel_latam", "https://upload.wikimedia.org/wikipedia/commons/thumb/2/23/Golf_Channel_Logo_2018.png/960px-Golf_Channel_Logo_2018.png"),
    ("sg_horse_tv", "https://i.imgur.com/nK4UUX4.png"),
    ("sg_htspor_tv", "https://www.htspor.com/images/manifest/social-share-logo.png"),
    ("sg_introuble", "https://i.imgur.com/a40chFI.png"),
    ("sg_itv_deportes", "https://iili.io/J1kV1Bn.png"),
    ("sg_jordan_sport", "https://i.imgur.com/2EmrZPQ.png"),
    ("sg_kcmn_ld6", "https://upload.wikimedia.org/wikipedia/commons/thumb/3/31/QVC_logo_2019.svg/960px-QVC_logo_2019.svg.png"),
    ("sg_khl", "https://i.imgur.com/RgdHdOV.png"),
    ("sg_khl_prime", "https://i.imgur.com/pwxT0ON.png"),
    ("sg_ktv_sport", "https://i.imgur.com/R1hGX1d.png"),
    ("sg_ktv_sport_plus", "https://i.imgur.com/l4oX0gf.png"),
    ("sg_laliga_tv", "https://i.imgur.com/ilay5Jr.png"),
    ("sg_lucha_libre_aaa", "https://i.imgur.com/Nc7K060.png"),
    ("sg_mnet_sport", "https://i.imgur.com/7k8ar1Z.png"),
    ("sg_madeinbo_tv", "https://i.imgur.com/47X44DD.png"),
    ("sg_match_strana", "https://i.imgur.com/X02s2UE.png"),
    ("sg_mma_tv_com", "https://i.imgur.com/QhdxNsB.png"),
    ("sg_mma_tv", "https://i.imgur.com/Qxco1eW.png"),
    ("sg_mnb_sport", "https://i.imgur.com/z854PC3.png"),
    ("sg_monterrico_tv", "https://i.imgur.com/SuVO9T7.png"),
    ("sg_more_than_sports", "https://i.imgur.com/SLrjImc.png"),
    ("sg_multivision_sports", "https://i.imgur.com/wLjSSo2.jpg"),
    ("sg_nautical_channel", "https://i.imgur.com/2ByDyzL.png"),
    ("sg_nba_tv_canada", "https://upload.wikimedia.org/wikipedia/en/a/a4/NBA_TV_Canada_2020.png"),
    ("sg_nhra_tv", "https://i.imgur.com/jZgcm4k.png"),
    ("sg_nudge_sports", "https://i.imgur.com/TW0hapZ.png"),
    ("sg_oman_sports_tv", "https://i.imgur.com/1omi7p8.png"),
    ("sg_ovacion_tv", "https://i.imgur.com/7Xndgxk.png"),
    ("sg_overtime", "https://i.imgur.com/9S9k4IK.png"),
    ("sg_pac12_insider", "https://i.imgur.com/736QREy.png"),
    ("sg_pbr_ridepass", "https://i.imgur.com/gUxH97E.png"),
    ("sg_persiana_fight", "https://www.lyngsat.com/logo/tv/pp/persiana-fight-fr.png"),
    ("sg_pga_tour", "https://i.imgur.com/J0TY9dG.png"),
    ("sg_pluto_futbol", "https://i.imgur.com/yJlY9Rr.png"),
    ("sg_polsat_sport_2", "https://i.imgur.com/myyWeXY.png"),
    ("sg_qazsport", "https://i.imgur.com/UDJ0P5Q.png"),
    ("sg_racer_select", "https://i.imgur.com/CurtYvn.png"),
    ("sg_realmadrid_tv", "https://i.imgur.com/5pMo7dL.png"),
    ("sg_red_bull_tv", "https://jiotvimages.cdn.jio.com/dare_images/images/Red_Bull_TV.png"),
    ("sg_rti_la_3", "https://i.imgur.com/HdNshgF.png"),
    ("sg_san_marino_rtv", "https://i.imgur.com/PGm944g.png"),
    ("sg_sky_racing_1", "https://i.imgur.com/Hf0EiaW.png"),
    ("sg_sky_racing_2", "https://i.imgur.com/TxQvFnQ.png"),
    ("sg_sony_ten_1", "https://xstreamcp-assets-msp.streamready.in/assets/LIVETV/LIVECHANNEL/LIVETV_LIVETVCHANNEL_SONY_SPORTS_TEN_1/images/LOGO_HD/image.png"),
    ("sg_sony_ten_1_hd", "https://xstreamcp-assets-msp.streamready.in/assets/LIVETV/LIVECHANNEL/LIVETV_LIVETVCHANNEL_SONY_SPORTS_TEN_1/images/LOGO_HD/image.png"),
    ("sg_sony_ten_2", "https://xstreamcp-assets-msp.streamready.in/assets/LIVETV/LIVECHANNEL/LIVETV_LIVETVCHANNEL_SONY_SPORTS_TEN_2/images/LOGO_HD/image.png"),
    ("sg_sony_ten_2_hd", "https://xstreamcp-assets-msp.streamready.in/assets/LIVETV/LIVECHANNEL/LIVETV_LIVETVCHANNEL_SONY_SPORTS_TEN_2/images/LOGO_HD/image.png"),
    ("sg_sony_ten_3", "https://dtil.tmsimg.com/assets/GNLZZGG0025TCMR.png?lock=720x540"),
    ("sg_sony_ten_3_hd", "https://dtil.tmsimg.com/assets/GNLZZGG0025TCMR.png?lock=720x540"),
    ("sg_sony_ten_4", "https://dtil.tmsimg.com/assets/GNLZZGG0025T4PV.png?lock=720x540"),
    ("sg_sony_ten_4_hd", "https://dtil.tmsimg.com/assets/s149166_ld_h15_aa.png?lock=720x540"),
    ("sg_sony_ten_5", "https://xstreamcp-assets-msp.streamready.in/assets/LIVETV/LIVECHANNEL/LIVETV_LIVETVCHANNEL_SONY_SPORTS_TEN_5/images/LOGO_HD/image.png"),
    ("sg_sony_ten_5_hd", "https://xstreamcp-assets-msp.streamready.in/assets/LIVETV/LIVECHANNEL/LIVETV_LIVETVCHANNEL_SONY_SPORTS_TEN_5/images/LOGO_HD/image.png"),
    ("sg_sos_kanal_plus", "https://i.imgur.com/9SD40uH.png"),
    ("sg_sport_1", "https://i.imgur.com/X5X3tKC.png"),
    ("sg_sport_italia", "https://i.imgur.com/0CJGGgd.png"),
    ("sg_sports_connect", "https://i.imgur.com/0sNWg54.png"),
    ("sg_stadium", "https://upload.wikimedia.org/wikipedia/en/thumb/5/53/Stadium_%28sports_network%29_logo.svg/960px-Stadium_%28sports_network%29_logo.svg.png"),
    ("sg_star_sports_1_hd", "https://i.imgur.com/E5jjKHI.png"),
    ("sg_star_sports_1_hindi", "https://xstreamcp-assets-msp.streamready.in/assets/LIVETV/LIVECHANNEL/LIVETV_LIVETVCHANNEL_STAR_SPORTS_1_HINDI/images/LOGO_HD/image.png"),
    ("sg_star_sports_2_hindi_hd", "https://i.imgur.com/kHerF19.png"),
    ("sg_strongman", "https://i.imgur.com/bVQBF6R.png"),
    ("sg_strongman_champions", "https://i.imgur.com/bVQBF6R.png"),
    ("sg_suspilne_sport", "https://i.imgur.com/16IhU0M.png"),
    ("sg_swerve_combat", "https://i.imgur.com/GT0Yi2T.png"),
    ("sg_talent_tv", "https://talenttv.lk/logo-footer.png"),
    ("sg_tele_rebelde", "https://i.imgur.com/M6wZzuz.png"),
    ("sg_teledeporte", "https://i.ibb.co/0jxLdjnY/TDP.png"),
    ("sg_teletrak", "https://i.imgur.com/NoJvlig.png"),
    ("sg_tennis_channel", "https://i.imgur.com/tsljAnY.png"),
    ("sg_tennis_channel_2", "https://i.imgur.com/tsljAnY.png"),
    ("sg_thmanyah_1", "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e9/Thmanyah_Logo.svg/500px-Thmanyah_Logo.svg.png"),
    ("sg_tigo_sports", "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3b/Tigo_Sports_2025.png/960px-Tigo_Sports_2025.png"),
    ("sg_tigo_sports_plus", "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3b/Tigo_Sports_2025.png/960px-Tigo_Sports_2025.png"),
    ("sg_tjk_tv", "https://i.imgur.com/3zHdkYG.png"),
    ("sg_tour_spot_tv", "https://imgur.com/khj869k.png"),
    ("sg_tr_sport", "https://i.imgur.com/ELXmaqg.png"),
    ("sg_trace_sport_stars_au", "https://i.imgur.com/FabFP5A.png"),
    ("sg_turf_movil", "https://i.imgur.com/TwIe4lK.png"),
    ("sg_turkmenistan_sport", "https://i.imgur.com/n6vITLu.png"),
    ("sg_tvmsport_plus", "https://i.imgur.com/YIreFti.png"),
    ("sg_tvr_sport", "https://upload.wikimedia.org/wikipedia/commons/thumb/9/93/TVR_Sport_Logo_2023.svg/960px-TVR_Sport_Logo_2023.svg.png"),
    ("sg_tvs_bowling", "https://www.watchyour.tv/channels/logo/tvs-bowling-network.jpg"),
    ("sg_tvs_boxing", "https://i.imgur.com/30ZoF75.png"),
    ("sg_tvs_classic_sports", "https://i.imgur.com/auR0Mi6.png"),
    ("sg_tvs_sports", "https://i.imgur.com/Lwwq62E.png"),
    ("sg_tvs_turbo", "https://i.imgur.com/7zYIbU1.png"),
    ("sg_tvs_women_sports", "https://i.imgur.com/8hC4PfF.png"),
    ("sg_tyc_sports", "https://upload.wikimedia.org/wikipedia/commons/thumb/5/54/TyC_Sports_logo.svg/960px-TyC_Sports_logo.svg.png"),
    ("sg_tyc_sports_latam", "https://upload.wikimedia.org/wikipedia/commons/thumb/5/54/TyC_Sports_logo.svg/960px-TyC_Sports_logo.svg.png"),
    ("sg_tyc_sports_usa", "https://upload.wikimedia.org/wikipedia/commons/thumb/5/54/TyC_Sports_logo.svg/960px-TyC_Sports_logo.svg.png"),
    ("sg_unbeaten_sports", "https://i.imgur.com/LmkNt3v.png"),
    ("sg_usa_network_east", "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d7/USA_Network_logo_%282016%29.svg/960px-USA_Network_logo_%282016%29.svg.png"),
    ("sg_w14dk_all_sports", "https://i.imgur.com/D4mZ8ll.png"),
    ("sg_willow_sports", "https://provider-static.plex.tv/epg/cms/production/acf3d1d8-c53e-49ca-86e9-0d9410b106b4/Willow_Sports_dark_Background_1500_1000_color.png"),
    ("sg_world_of_freesports", "https://i.imgur.com/lta5Mog.png"),
    ("sg_world_of_freesports_2", "https://i.imgur.com/lta5Mog.png"),
    ("sg_world_poker_tour", "https://i.imgur.com/98kLMjj.png"),
    ("sg_world_poker_tour_hd", "https://i.imgur.com/98kLMjj.png"),
    ("sg_astrakhan_sport", "https://i.imgur.com/BKaEtqL.png"),
    ("sg_belarus_5", "https://i.imgur.com/NJsRFud.png"),
    ("sg_belarus_5_int", "https://i.imgur.com/NJsRFud.png"),
    ("sg_boks_tv", "https://i.imgur.com/R1UjyfX.png"),
    ("sg_match_arena", "https://i.imgur.com/udTzwzu.png"),
    ("sg_match_boets", "https://i.imgur.com/DogOkA4.png"),
    ("sg_match_igra", "https://i.imgur.com/5XWpF19.png"),
    ("sg_match_planeta", "https://i.imgur.com/vhyMb9D.png"),
    ("sg_russkiy_ekstrim", "https://i.imgur.com/hJK7mOW.png"),
    ("sg_futbol_hd", "https://i.imgur.com/pEuaZVx.png"),
]

HEADERS = {"User-Agent": "Mozilla/5.0"}

def make_square_thumbnail(img: Image.Image, size: int, bg: tuple) -> Image.Image:
    """Fit image into a square with a solid background, preserving aspect ratio."""
    img = img.convert("RGBA")
    img.thumbnail((size, size), Image.LANCZOS)
    canvas = Image.new("RGBA", (size, size), (*bg, 255))
    offset = ((size - img.width) // 2, (size - img.height) // 2)
    canvas.paste(img, offset, img)
    return canvas.convert("RGB")

done = 0
skipped = 0
failed = 0

for channel_id, url in CHANNELS:
    out_path = LOGOS_DIR / f"{channel_id}.png"
    if out_path.exists():
        skipped += 1
        continue
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = resp.read()
        img = Image.open(io.BytesIO(data))
        thumb = make_square_thumbnail(img, 256, BG_COLOR)
        thumb.save(out_path, "PNG", optimize=True)
        done += 1
        print(f"  OK  {channel_id}")
    except Exception as e:
        failed += 1
        print(f"  FAIL {channel_id}: {e}")

print(f"\nDone: {done} | Skipped: {skipped} | Failed: {failed}")
