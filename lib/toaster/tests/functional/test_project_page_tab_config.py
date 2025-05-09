#! /usr/bin/env python3 #
# BitBake Toaster UI tests implementation
#
# Copyright (C) 2023 Savoir-faire Linux
#
# SPDX-License-Identifier: GPL-2.0-only
#

import string
import time
import pytest
from django.urls import reverse
from selenium.webdriver import Keys
from selenium.webdriver.support.select import Select
from selenium.common.exceptions import ElementClickInterceptedException, NoSuchElementException, TimeoutException
from tests.functional.functional_helpers import SeleniumFunctionalTestCase
from selenium.webdriver.common.by import By

from .utils import get_projectId_from_url, wait_until_build, wait_until_build_cancelled

class TestProjectConfigTabBase(SeleniumFunctionalTestCase):
    PROJECT_NAME = 'TestProjectConfigTab'
    project_id = None

    def _navigate_to_project_page(self):
        # Navigate to project page
        if TestProjectConfigTabBase.project_id is None:
            TestProjectConfigTabBase.project_id = self.create_new_project(self.PROJECT_NAME, '3', None, True)
        url = reverse('project', args=(TestProjectConfigTabBase.project_id,))
        self.get(url)
        self.wait_until_visible('#config-nav')

    def _create_builds(self):
        # check search box can be use to build recipes
        search_box = self.find('#build-input')
        search_box.send_keys('foo')
        self.find('#build-button').click()
        self.wait_until_present('#latest-builds')
        # loop until reach the parsing state
        wait_until_build(self, 'queued cloning starting parsing failed')
        lastest_builds = self.driver.find_elements(
            By.XPATH,
            '//div[@id="latest-builds"]/div',
        )
        last_build = lastest_builds[0]
        self.assertIn(
            'foo', str(last_build.text)
        )
        last_build = lastest_builds[0]
        try:
            cancel_button = last_build.find_element(
                By.XPATH,
                '//span[@class="cancel-build-btn pull-right alert-link"]',
            )
            cancel_button.click()
        except NoSuchElementException:
            # Skip if the build is already cancelled
            pass
        wait_until_build_cancelled(self)

    def _get_tabs(self):
        # tabs links list
        return self.driver.find_elements(
            By.XPATH,
            '//div[@id="project-topbar"]//li'
        )

    def _get_config_nav_item(self, index):
        config_nav = self.find('#config-nav')
        return config_nav.find_elements(By.TAG_NAME, 'li')[index]

class TestProjectConfigTab(TestProjectConfigTabBase):

    def test_project_config_nav(self):
        """ Test project config tab navigation:
        - Check if the menu is displayed and contains the right elements:
            - Configuration
            - COMPATIBLE METADATA
            - Custom images
            - Image recipes
            - Software recipes
            - Machines
            - Layers
            - Distro
            - EXTRA CONFIGURATION
            - Bitbake variables
            - Actions
            - Delete project
        """
        self._navigate_to_project_page()

        def _get_config_nav_item(index):
            config_nav = self.find('#config-nav')
            return config_nav.find_elements(By.TAG_NAME, 'li')[index]

        def check_config_nav_item(index, item_name, url):
            item = _get_config_nav_item(index)
            self.assertIn(item_name, item.text)
            self.assertEqual(item.get_attribute('class'), 'active')
            self.assertIn(url, self.driver.current_url)

        # check if the menu contains the right elements
        # COMPATIBLE METADATA
        compatible_metadata = _get_config_nav_item(1)
        self.assertIn(
            "compatible metadata", compatible_metadata.text.lower()
        )
        # EXTRA CONFIGURATION
        extra_configuration = _get_config_nav_item(8)
        self.assertIn(
            "extra configuration", extra_configuration.text.lower()
        )
        # Actions
        actions = _get_config_nav_item(10)
        self.assertIn("actions", str(actions.text).lower())

        conf_nav_list = [
            # config
            [0, 'Configuration',
                f"/toastergui/project/{TestProjectConfigTabBase.project_id}"],
            # custom images
            [2, 'Custom images',
                f"/toastergui/project/{TestProjectConfigTabBase.project_id}/customimages"],
            # image recipes
            [3, 'Image recipes',
                f"/toastergui/project/{TestProjectConfigTabBase.project_id}/images"],
            # software recipes
            [4, 'Software recipes',
                f"/toastergui/project/{TestProjectConfigTabBase.project_id}/softwarerecipes"],
            # machines
            [5, 'Machines',
                f"/toastergui/project/{TestProjectConfigTabBase.project_id}/machines"],
            # layers
            [6, 'Layers',
                f"/toastergui/project/{TestProjectConfigTabBase.project_id}/layers"],
            # distro
            [7, 'Distros',
                f"/toastergui/project/{TestProjectConfigTabBase.project_id}/distros"],
            #  [9, 'BitBake variables', f"/toastergui/project/{TestProjectConfigTabBase.project_id}/configuration"],  # bitbake variables
        ]
        for index, item_name, url in conf_nav_list:
            item = _get_config_nav_item(index)
            if item.get_attribute('class') != 'active':
                item.click()
            check_config_nav_item(index, item_name, url)

    def test_image_recipe_editColumn(self):
        """ Test the edit column feature in image recipe table on project page """
        def test_edit_column(check_box_id):
            # Check that we can hide/show table column
            check_box = self.find(f'#{check_box_id}')
            th_class = str(check_box_id).replace('checkbox-', '')
            if check_box.is_selected():
                # check if column is visible in table
                self.assertTrue(
                    self.find(
                        f'#imagerecipestable thead th.{th_class}'
                    ).is_displayed(),
                    f"The {th_class} column is checked in EditColumn dropdown, but it's not visible in table"
                )
                check_box.click()
                # check if column is hidden in table
                self.assertFalse(
                    self.find(
                        f'#imagerecipestable thead th.{th_class}'
                    ).is_displayed(),
                    f"The {th_class} column is unchecked in EditColumn dropdown, but it's visible in table"
                )
            else:
                # check if column is hidden in table
                self.assertFalse(
                    self.find(
                        f'#imagerecipestable thead th.{th_class}'
                    ).is_displayed(),
                    f"The {th_class} column is unchecked in EditColumn dropdown, but it's visible in table"
                )
                check_box.click()
                # check if column is visible in table
                self.assertTrue(
                    self.find(
                        f'#imagerecipestable thead th.{th_class}'
                    ).is_displayed(),
                    f"The {th_class} column is checked in EditColumn dropdown, but it's not visible in table"
                )

        self._navigate_to_project_page()
        # navigate to project image recipe page
        recipe_image_page_link = self._get_config_nav_item(3)
        recipe_image_page_link.click()
        self.wait_until_present('#imagerecipestable tbody tr')

        # Check edit column
        edit_column = self.find('#edit-columns-button')
        self.assertTrue(edit_column.is_displayed())
        edit_column.click()
        # Check dropdown is visible
        self.wait_until_visible('ul.dropdown-menu.editcol')

        # Check that we can hide the edit column
        test_edit_column('checkbox-get_description_or_summary')
        test_edit_column('checkbox-layer_version__get_vcs_reference')
        test_edit_column('checkbox-layer_version__layer__name')
        test_edit_column('checkbox-license')
        test_edit_column('checkbox-recipe-file')
        test_edit_column('checkbox-section')
        test_edit_column('checkbox-version')

    def test_image_recipe_show_rows(self):
        """ Test the show rows feature in image recipe table on project page """
        def test_show_rows(row_to_show, show_row_link):
            # Check that we can show rows == row_to_show
            show_row_link.select_by_value(str(row_to_show))
            self.wait_until_visible('#imagerecipestable tbody tr')
            # check at least some rows are visible
            self.assertTrue(
                len(self.find_all('#imagerecipestable tbody tr'))  > 0
            )

        self._navigate_to_project_page()
        # navigate to project image recipe page
        recipe_image_page_link = self._get_config_nav_item(3)
        recipe_image_page_link.click()
        self.wait_until_present('#imagerecipestable tbody tr')

        show_rows = self.driver.find_elements(
            By.XPATH,
            '//select[@class="form-control pagesize-imagerecipestable"]'
        )
        # Check show rows
        for show_row_link in show_rows:
            show_row_link = Select(show_row_link)
            test_show_rows(10, show_row_link)
            test_show_rows(25, show_row_link)
            test_show_rows(50, show_row_link)
            test_show_rows(100, show_row_link)
            test_show_rows(150, show_row_link)

    def test_project_config_tab_right_section(self):
        """ Test project config tab right section contains five blocks:
            - Machine:
                - check 'Machine' is displayed
                - check can change Machine
            - Distro:
                - check 'Distro' is displayed
                - check can change Distro
            - Most built recipes:
                - check 'Most built recipes' is displayed
                - check can select a recipe and build it
            - Project release:
                - check 'Project release' is displayed
                - check project has right release displayed
            - Layers:
                - check can add a layer if exists
                - check at least three layers are displayed
                    - openembedded-core
                    - meta-poky
                    - meta-yocto-bsp
        """
        project_id = self.create_new_project(self.PROJECT_NAME + "-ST", '3', None, True)
        url = reverse('project', args=(project_id,))
        self.get(url)
        self.wait_until_visible('#config-nav')

        # check if the menu is displayed
        self.wait_until_visible('#project-page')
        block_l = self.driver.find_element(
            By.XPATH, '//*[@id="project-page"]/div[2]')
        project_release = self.driver.find_element(
            By.XPATH, '//*[@id="project-page"]/div[1]/div[4]')
        layers = block_l.find_element(By.ID, 'layer-container')

        def check_machine_distro(self, item_name, new_item_name, block_id):
            block = self.find(f'#{block_id}')
            title = block.find_element(By.TAG_NAME, 'h3')
            self.assertIn(item_name.capitalize(), title.text)
            edit_btn = self.find(f'#change-{item_name}-toggle')
            edit_btn.click()
            self.wait_until_visible(f'#{item_name}-change-input')
            name_input = self.find(f'#{item_name}-change-input')
            name_input.clear()
            name_input.send_keys(new_item_name)
            change_btn = self.find(f'#{item_name}-change-btn')
            change_btn.click()
            self.wait_until_visible(f'#project-{item_name}-name')
            project_name = self.find(f'#project-{item_name}-name')
            self.assertIn(new_item_name, project_name.text)
            # check change notificaiton is displayed
            change_notification = self.find('#change-notification')
            self.assertIn(
                f'You have changed the {item_name} to: {new_item_name}', change_notification.text
            )
            hide_button = self.find('#hide-alert')
            hide_button.click()
            self.wait_until_not_visible('#change-notification')

        # Machine
        check_machine_distro(self, 'machine', 'qemux86-64', 'machine-section')
        # Distro
        check_machine_distro(self, 'distro', 'poky-altcfg', 'distro-section')

        # Project release
        title = project_release.find_element(By.TAG_NAME, 'h3')
        self.assertIn("Project release", title.text)
        self.assertIn(
            "Yocto Project master", self.find('#project-release-title').text
        )
        # Layers
        title = layers.find_element(By.TAG_NAME, 'h3')
        self.assertIn("Layers", title.text)
        self.wait_until_clickable('#layer-add-input')
        # check at least three layers are displayed
        # openembedded-core
        # meta-poky
        # meta-yocto-bsp
        layer_list_items = []
        starttime = time.time()
        while len(layer_list_items) < 3:
            layers_list = self.driver.find_element(By.ID, 'layers-in-project-list')
            layer_list_items = layers_list.find_elements(By.TAG_NAME, 'li')
            if time.time() > (starttime + 30):
                self.fail("Layer list didn't contain at least 3 items within 30s (contained %d)" % len(layer_list_items))

        # remove all layers except the first three layers
        for i in range(3, len(layer_list_items)):
            layer_list_items[i].find_element(By.TAG_NAME, 'span').click()

        # check can add a layer if exists
        add_layer_input = layers.find_element(By.ID, 'layer-add-input')
        add_layer_input.send_keys('meta-oe')
        self.wait_until_visible('#layer-container > form > div > span > div')
        self.wait_until_visible('.dropdown-menu')
        finder = lambda driver: driver.find_element(By.XPATH, '//*[@id="layer-container"]/form/div/span/div/div/div')
        dropdown_item = self.wait_until_element_clickable(finder)
        dropdown_item.click()
        self.wait_until_clickable('#add-layer-btn')
        add_layer_btn = layers.find_element(By.ID, 'add-layer-btn')
        add_layer_btn.click()
        self.wait_until_visible('#layers-in-project-list')

        # check layer is added
        layer_list_items = []
        starttime = time.time()
        while len(layer_list_items) < 4:
            layers_list = self.driver.find_element(By.ID, 'layers-in-project-list')
            layer_list_items = layers_list.find_elements(By.TAG_NAME, 'li')
            if time.time() > (starttime + 30):
                self.fail("Layer list didn't contain at least 4 items within 30s (contained %d)" % len(layer_list_items))

    def test_project_page_tab_importlayer(self):
        """ Test project page tab import layer """
        self._navigate_to_project_page()
        # navigate to "Import layers" tab
        import_layers_tab = self._get_tabs()[2]
        import_layers_tab.find_element(By.TAG_NAME, 'a').click()
        self.wait_until_visible('#layer-git-repo-url')

        # Check git repo radio button
        git_repo_radio = self.find('#git-repo-radio')
        git_repo_radio.click()

        # Set git repo url
        input_repo_url = self.find('#layer-git-repo-url')
        input_repo_url.send_keys('git://git.yoctoproject.org/meta-fake')
        # Blur the input to trigger the validation
        input_repo_url.send_keys(Keys.TAB)

        # Check name is set
        input_layer_name = self.find('#import-layer-name')
        self.assertTrue(input_layer_name.get_attribute('value') == 'meta-fake')

        # Set branch
        input_branch = self.find('#layer-git-ref')
        input_branch.send_keys('master')

        # Import layer
        self.find('#import-and-add-btn').click()

        # Check layer is added
        self.wait_until_visible('#layer-container')
        block_l = self.driver.find_element(
            By.XPATH, '//*[@id="project-page"]/div[2]')
        layers = block_l.find_element(By.ID, 'layer-container')
        layers_list = layers.find_element(By.ID, 'layers-in-project-list')
        layers_list_items = layers_list.find_elements(By.TAG_NAME, 'li')
        self.assertIn(
            'meta-fake', str(layers_list_items[-1].text)
        )

    def test_project_page_custom_image_no_image(self):
        """ Test project page tab "New custom image" when no custom image """
        project_id = self.create_new_project(self.PROJECT_NAME + "-CustomImage", '3', None, True)
        url = reverse('project', args=(project_id,))
        self.get(url)
        self.wait_until_visible('#config-nav')

        # navigate to "Custom image" tab
        custom_image_section = self._get_config_nav_item(2)
        custom_image_section.click()
        self.wait_until_visible('#empty-state-customimagestable')

        # Check message when no custom image
        self.assertIn(
            "You have not created any custom images yet.", str(
                self.find('#empty-state-customimagestable').text
            )
        )
        div_empty_msg = self.find('#empty-state-customimagestable')
        link_create_custom_image = div_empty_msg.find_element(
            By.TAG_NAME, 'a')
        self.assertTrue(TestProjectConfigTabBase.project_id is not None)
        self.assertIn(
            f"/toastergui/project/{project_id}/newcustomimage", str(
                link_create_custom_image.get_attribute('href')
            )
        )
        self.assertIn(
            "Create your first custom image", str(
                link_create_custom_image.text
            )
        )

    def test_project_page_image_recipe(self):
        """ Test project page section images
            - Check image recipes are displayed
            - Check search input
            - Check image recipe build button works
            - Check image recipe table features(show/hide column, pagination)
        """
        self._navigate_to_project_page()
        # navigate to "Images section"
        images_section = self._get_config_nav_item(3)
        images_section.click()
        self.wait_until_visible('#imagerecipestable')
        rows = self.find_all('#imagerecipestable tbody tr')
        self.assertTrue(len(rows) > 0)

        # Test search input
        self.wait_until_visible('#search-input-imagerecipestable')
        recipe_input = self.find('#search-input-imagerecipestable')
        recipe_input.send_keys('core-image-minimal')
        self.find('#search-submit-imagerecipestable').click()
        self.wait_until_visible('#imagerecipestable tbody tr')
        rows = self.find_all('#imagerecipestable tbody tr')
        self.assertTrue(len(rows) > 0)

@pytest.mark.django_db
@pytest.mark.order("last") 
class TestProjectConfigTabDB(TestProjectConfigTabBase):

    def test_most_build_recipes(self):
        """ Test most build recipes block contains"""
        def rebuild_from_most_build_recipes(recipe_list_items):
            checkbox = recipe_list_items[0].find_element(By.TAG_NAME, 'input')
            checkbox.click()
            build_btn = self.find('#freq-build-btn')
            build_btn.click()
            self.wait_until_visible('#latest-builds')
            wait_until_build(self, 'queued cloning starting parsing failed')
            lastest_builds = self.driver.find_elements(
                By.XPATH,
                '//div[@id="latest-builds"]/div'
            )
            self.assertTrue(len(lastest_builds) >= 2)
            last_build = lastest_builds[0]
            try:
                cancel_button = last_build.find_element(
                    By.XPATH,
                    '//span[@class="cancel-build-btn pull-right alert-link"]',
                )
                cancel_button.click()
            except NoSuchElementException:
                # Skip if the build is already cancelled
                pass
            wait_until_build_cancelled(self)

        # Create a new project for remaining asserts
        project_id = self.create_new_project(self.PROJECT_NAME + "-MostBuilt", '2', None, True)
        url = reverse('project', args=(project_id,))
        self.get(url)
        self.wait_until_visible('#config-nav')

        current_url = self.driver.current_url
        url = current_url.split('?')[0]

        # Create a new builds
        self._create_builds()

        # back to project page
        self.driver.get(url)

        self.wait_until_visible('#project-page')

        # Most built recipes
        most_built_recipes = self.driver.find_element(
            By.XPATH, '//*[@id="project-page"]/div[1]/div[3]')
        title = most_built_recipes.find_element(By.TAG_NAME, 'h3')
        self.assertIn("Most built recipes", title.text)
        # check can select a recipe and build it
        self.wait_until_visible('#freq-build-list')
        recipe_list = self.find('#freq-build-list')
        recipe_list_items = recipe_list.find_elements(By.TAG_NAME, 'li')
        self.assertTrue(
            len(recipe_list_items) > 0,
            msg="No recipes found in the most built recipes list",
        )
        rebuild_from_most_build_recipes(recipe_list_items)

