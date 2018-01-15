#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from busmap import htmlutil
import time
import os
import os
import io
from PIL import Image

ANIM_DIR = "./anim"

if not os.path.exists(ANIM_DIR):
    os.mkdir(ANIM_DIR)


print("Starting browser...")



def main():
    browser = htmlutil.HTMLReader(
        "file://" + os.path.abspath("./www/map.html"),
        width=720,
        height=720
    )
    browser.driver.get_screenshot_as_file(os.path.join(ANIM_DIR, "a.png"))

    # アニメーションモードのスタート
    print("Starting anim mode")
    browser.driver.find_element_by_css_selector('.rendermode_btn').click()

    browser.driver.get_screenshot_as_file(os.path.join(ANIM_DIR, "amode.png"))

    step_button = browser.driver.find_element_by_css_selector('.animation-rendering-step')

    num_all_frames = 6*60*24
    for i in range(0, num_all_frames):
        filename = os.path.join(ANIM_DIR, "r-{0:06}.jpg".format(i))
        cropbox = (16, 60, 1295, 1338)

        print("Rendering {0}/{1}".format(i, num_all_frames))
        step_button.click()
        pngstrm = io.BytesIO(browser.driver.get_screenshot_as_png())
        img = Image.open(pngstrm)
        region = img.crop(cropbox)
        region_noalpha = region.convert("RGB")
        region_noalpha.save(filename, 'JPEG', optimize=True, quality=80)
        img.close()
        region.close()
        region_noalpha.close()
        pngstrm.close()


main()

