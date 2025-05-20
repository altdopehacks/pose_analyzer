import unittest
import os
import json
import csv
from datetime import datetime
from app import save_landmarks_data # Assuming functions are in app.py

# Mock or dummy data for testing
DUMMY_FRAMES_DATA = [
    [ # Frame 0
        {'landmark_id': 0, 'x': 0.1, 'y': 0.2, 'z': 0.3, 'visibility': 0.99},
        {'landmark_id': 1, 'x': 0.2, 'y': 0.3, 'z': 0.4, 'visibility': 0.98},
    ],
    [ # Frame 1
        {'landmark_id': 0, 'x': 0.15, 'y': 0.25, 'z': 0.35, 'visibility': 0.97},
        {'landmark_id': 1, 'x': 0.25, 'y': 0.35, 'z': 0.45, 'visibility': 0.96},
    ]
]
ORIGINAL_VIDEO_PATH_DUMMY = "test_video.mp4"
OUTPUT_DIR_LANDMARKS_TEST = "output_test/landmarks_data/"

class TestApp(unittest.TestCase):

    def setUp(self):
        # Create dummy output directory for tests
        os.makedirs(OUTPUT_DIR_LANDMARKS_TEST, exist_ok=True)
        # Clean up any files from previous tests in the specific test output dir
        for f in os.listdir(OUTPUT_DIR_LANDMARKS_TEST):
            os.remove(os.path.join(OUTPUT_DIR_LANDMARKS_TEST, f))


    def tearDown(self):
        # Clean up dummy output directory after tests
        if os.path.exists(OUTPUT_DIR_LANDMARKS_TEST):
            for f in os.listdir(OUTPUT_DIR_LANDMARKS_TEST):
                os.remove(os.path.join(OUTPUT_DIR_LANDMARKS_TEST, f))
            os.rmdir(OUTPUT_DIR_LANDMARKS_TEST)
            # Also remove parent if it was created and is empty
            if OUTPUT_DIR_LANDMARKS_TEST.startswith("output_test/") and os.path.exists("output_test") and not os.listdir("output_test"):
                os.rmdir("output_test")


    def test_save_landmarks_data_json_filename_and_creation(self):
        timestamp_before = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = save_landmarks_data(
            DUMMY_FRAMES_DATA, "json", ORIGINAL_VIDEO_PATH_DUMMY, OUTPUT_DIR_LANDMARKS_TEST
        )
        self.assertTrue(os.path.exists(file_path))
        expected_filename_part = os.path.splitext(os.path.basename(ORIGINAL_VIDEO_PATH_DUMMY))[0]
        self.assertIn(expected_filename_part, os.path.basename(file_path))
        self.assertIn("_landmarks.json", os.path.basename(file_path))
        # Check if timestamp is close
        # This is a bit tricky due to potential slight delay.
        # A more robust way would be to mock datetime.now() if possible.
        # Checking a significant portion of the timestamp string for a match.
        # Example: file_Y20231027_123456_... vs expected_Y20231027_12345...
        # We will check the first 12 characters of the timestamp part (YYYYMMDD_HHM)
        # The filename format is {original_filename_base}_{timestamp}_landmarks.{output_format}
        # So, the part to check is {expected_filename_part}_YYYYMMDD_HHM
        # We need to extract the timestamp from the actual filename to compare
        filename_stem = os.path.basename(file_path)
        # Expected pattern: test_video_YYYYMMDD_HHMMSS_landmarks.json
        # We look for test_video_ followed by the timestamp part
        # The timestamp part will be between "{expected_filename_part}_" and "_landmarks.json"
        
        # A simpler check: Ensure the timestamp is within a few seconds.
        # For this test, we'll check if the generated timestamp starts with the same YYYYMMDD_HHMM part as timestamp_before
        # This might fail if the test runs exactly at the turn of a second.
        # A more robust check would involve mocking datetime.now() or comparing datetime objects with a small delta.
        generated_timestamp_str = filename_stem.split('_')[2] # Assuming "test"_"video"_"YYYYMMDD"_"HHMMSS"_"landmarks.json" or "test_video"_"YYYYMMDD"_"HHMMSS"
        
        # Corrected extraction based on filename pattern: {original_filename_base}_{timestamp}_landmarks.{output_format}
        # original_filename_base can have underscores.
        # Let's find the part between "test_video_" and "_landmarks.json"
        prefix = f"{expected_filename_part}_"
        suffix = "_landmarks.json"
        self.assertTrue(filename_stem.startswith(prefix))
        self.assertTrue(filename_stem.endswith(suffix))
        generated_timestamp_in_filename = filename_stem[len(prefix):-len(suffix)]

        self.assertTrue(generated_timestamp_in_filename.startswith(timestamp_before[:13])) # YYYYMMDD_HHMM (first 13 chars)


        # Basic content check
        with open(file_path, 'r') as f:
            data = json.load(f)
        self.assertEqual(len(data), len(DUMMY_FRAMES_DATA))
        self.assertEqual(len(data[0]), len(DUMMY_FRAMES_DATA[0]))


    def test_save_landmarks_data_csv_filename_and_structure(self):
        file_path = save_landmarks_data(
            DUMMY_FRAMES_DATA, "csv", ORIGINAL_VIDEO_PATH_DUMMY, OUTPUT_DIR_LANDMARKS_TEST
        )
        self.assertTrue(os.path.exists(file_path))
        expected_filename_part = os.path.splitext(os.path.basename(ORIGINAL_VIDEO_PATH_DUMMY))[0]
        self.assertIn(expected_filename_part, os.path.basename(file_path))
        self.assertIn("_landmarks.csv", os.path.basename(file_path))

        # Check CSV content
        with open(file_path, 'r', newline='') as f:
            reader = csv.reader(f)
            header = next(reader)
            self.assertEqual(header, ['frame_index', 'landmark_id', 'x', 'y', 'z', 'visibility'])
            
            row_count = 0
            for frame_idx, frame_landmarks in enumerate(DUMMY_FRAMES_DATA):
                for landmark in frame_landmarks:
                    row = next(reader)
                    self.assertEqual(int(row[0]), frame_idx)
                    self.assertEqual(int(row[1]), landmark['landmark_id'])
                    self.assertEqual(float(row[2]), landmark['x'])
                    # Add checks for y, z, visibility for completeness
                    self.assertEqual(float(row[3]), landmark['y'])
                    self.assertEqual(float(row[4]), landmark['z'])
                    self.assertEqual(float(row[5]), landmark['visibility'])
                    row_count +=1
            self.assertEqual(row_count, sum(len(frame) for frame in DUMMY_FRAMES_DATA))


if __name__ == '__main__':
    unittest.main()
